"""
inference.py — Baseline AI agent for MediRoute OpenEnv.

Connects to any OpenAI-compatible endpoint (including Hugging Face TGI,
vLLM, or the official OpenAI API) and runs the agent across all three
difficulty tasks, printing structured logs.

Environment variables (set before running):
    OPENAI_API_KEY   – API key (use 'EMPTY' for local / HF endpoints)
    API_BASE_URL     – Base URL, e.g. https://api-inference.huggingface.co/v1
    MODEL_NAME       – Model identifier, e.g. mistralai/Mistral-7B-Instruct-v0.3
    HF_TOKEN         – (Optional) Hugging Face token for gated models

Usage:
    python inference.py
    python inference.py --difficulty easy
    python inference.py --difficulty all
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# OpenAI SDK is only required for the LLM agent mode.
if TYPE_CHECKING:
    from openai import OpenAI  # pragma: no cover
else:
    OpenAI = Any  # type: ignore[misc,assignment]

from environment import MediRouteEnv
from models import Action, VALID_ACTION_TYPES

# ─────────────────────────────────────────────
#  Configuration from environment variables
# ─────────────────────────────────────────────

API_KEY: str = os.getenv("OPENAI_API_KEY", "EMPTY")
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN: str = os.getenv("HF_TOKEN", "")

# If HF_TOKEN is set, prefer it as the API key for HF endpoints
if HF_TOKEN and API_KEY == "EMPTY":
    API_KEY = HF_TOKEN

MAX_STEPS_PER_EPISODE: int = 8
ALL_DIFFICULTIES: List[str] = ["easy", "medium", "hard"]


# ─────────────────────────────────────────────
#  Prompt engineering
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are MediRoute, an AI medical triage and routing agent.
Your goal is to help patients by:
1. Analysing their symptoms and lab reports to determine severity.
2. Recommending the correct medical specialist.
3. Selecting the best nearby hospital.
4. Booking appointments or dispatching ambulances as appropriate.

You must respond with a single JSON object containing exactly two keys:
  "action_type" : one of [analyze_symptoms, request_more_info, recommend_specialist,
                           select_hospital, book_appointment, call_ambulance,
                           provide_temp_guidance]
  "target"      : a string value relevant to the action, or null

Severity levels for analyze_symptoms: low | moderate | high | critical

Rules:
- For life-threatening emergencies (SpO₂ < 85 %, unconscious, etc.) → call_ambulance.
- Do NOT book an appointment in a critical emergency.
- Pick the FIRST hospital in the nearby_hospitals list as the best option.
- Stop after taking a terminal action (book_appointment or call_ambulance).
- Never repeat the same action twice.
"""


def build_user_message(obs, step: int) -> str:
    return f"""Step {step} — Patient Status:

Symptoms       : {obs.symptoms}
Lab Results    : {json.dumps(obs.lab_report_summary, indent=2)}
Severity Score : {obs.severity_score:.2f}
Location       : {obs.location}
Nearby Hospitals (in order of proximity/quality):
  {chr(10).join(f'  {i+1}. {h}' for i, h in enumerate(obs.nearby_hospitals))}
Available Specialists:
  {chr(10).join(f'  - {s}' for s in obs.available_specialists)}
Actions already taken: {obs.previous_actions or '(none)'}

What is your next action? Respond ONLY with valid JSON.
"""


# ─────────────────────────────────────────────
#  Agent loop
# ─────────────────────────────────────────────

def parse_action(response_text: str) -> Optional[Action]:
    """Extract a valid Action from the model's raw JSON response."""
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:])

    # Extract the first JSON object defensively (models sometimes add extra prose).
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        text = m.group(0)

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        # Keep logs compatible with strict parsers: no free-form prefixes.
        print(f"[STEP] event=parse_error detail={str(exc)[:120]!r}")
        return None

    action_type = str(data.get("action_type", "request_more_info")).strip()
    target = data.get("target")
    if action_type not in VALID_ACTION_TYPES:
        return Action(action_type="request_more_info", target=None)
    if target is not None and not isinstance(target, str):
        # Keep schema strict: targets are strings or null.
        target = str(target)
    return Action(action_type=action_type, target=target)


def rules_agent(obs) -> Action:
    """
    Deterministic baseline policy.
    Designed to be fully offline and reproducible for judge evaluation.
    """
    labs = obs.lab_report_summary or {}
    symptoms = (obs.symptoms or "").lower()

    # 1) Emergency detection / severity inference
    spo2_raw = str(labs.get("spo2", "")).lower()
    gcs_raw = str(labs.get("consciousness", "")).lower()
    emergency_signals = any(
        s in spo2_raw for s in ["78", "79", "80", "81", "82", "83", "84"]
    ) or ("unresponsive" in gcs_raw) or ("cyanotic" in symptoms) or ("collapse" in symptoms)

    if not any(a.startswith("analyze_symptoms:") for a in obs.previous_actions):
        if emergency_signals:
            return Action(action_type="analyze_symptoms", target="critical")
        # STEMI-ish signals
        ecg = str(labs.get("ecg_finding", "")).lower()
        troponin = str(labs.get("troponin_i", "")).lower()
        if "st-segment elevation" in ecg or "elevated" in troponin:
            return Action(action_type="analyze_symptoms", target="high")
        # Default outpatient
        return Action(action_type="analyze_symptoms", target="low")

    # 2) Route to specialist
    if not any(a.startswith("recommend_specialist:") for a in obs.previous_actions):
        if emergency_signals:
            return Action(action_type="recommend_specialist", target="Emergency Doctor")
        # Cardiology cues
        ecg = str(labs.get("ecg_finding", "")).lower()
        troponin = str(labs.get("troponin_i", "")).lower()
        if "st-segment elevation" in ecg or "elevated" in troponin:
            return Action(action_type="recommend_specialist", target="Cardiologist")
        return Action(action_type="recommend_specialist", target="General Physician")

    # 3) Choose hospital (prefer first listed)
    if not any(a.startswith("select_hospital:") for a in obs.previous_actions):
        best = obs.nearby_hospitals[0] if obs.nearby_hospitals else "General Hospital"
        return Action(action_type="select_hospital", target=best)

    # 4) Close episode
    if emergency_signals:
        return Action(action_type="call_ambulance", target=None)
    return Action(action_type="book_appointment", target=None)


def run_episode(client: Optional[OpenAI], difficulty: str, agent: str) -> Dict[str, Any]:
    """Run a complete episode for the given difficulty and return the summary."""
    env = MediRouteEnv()
    obs = env.reset(difficulty=difficulty)
    conversation: List[Dict[str, str]] = []
    step = 0
    episode_start = time.time()

    print(f"[START] difficulty={difficulty.upper()} agent={agent} symptoms={obs.symptoms!r}")

    while step < MAX_STEPS_PER_EPISODE:
        step += 1
        if agent == "rules":
            action = rules_agent(obs)
        else:
            user_msg = build_user_message(obs, step)
            conversation.append({"role": "user", "content": user_msg})

            # ── Call the model ────────────────────────────────────────────────
            assistant_text = ""
            for attempt in range(2):
                try:
                    if client is None:
                        raise RuntimeError("OpenAI client not initialized.")
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation,
                        temperature=0.0,   # deterministic (to the extent the backend supports it)
                        max_tokens=256,
                    )
                    assistant_text = response.choices[0].message.content or ""
                except Exception as exc:
                    print(f"[STEP] step={step} event=llm_error detail={str(exc)[:160]!r}")
                    assistant_text = ""
                    break

                action = parse_action(assistant_text)
                if action is not None:
                    break

                # One corrective retry: ask for strict JSON only.
                conversation.append({"role": "assistant", "content": assistant_text})
                conversation.append(
                    {
                        "role": "user",
                        "content": "Your last response was invalid. Respond with ONLY a JSON object with keys action_type and target.",
                    }
                )

            if assistant_text:
                conversation.append({"role": "assistant", "content": assistant_text})

            if action is None:
                action = Action(action_type="request_more_info", target=None)

        # ── Step environment ──────────────────────────────────────────────────
        result = env.step(action)

        reward_sign = "+" if result.reward >= 0 else ""
        print(
            f"[STEP {step}] action={action.action_type}  "
            f"target={action.target!r}  "
            f"reward={reward_sign}{result.reward:.2f}  "
            f"total={result.info.get('total_reward', 0):.2f}  "
            f"done={result.done}"
        )

        obs = result.observation

        if result.done:
            break

    elapsed = time.time() - episode_start
    summary = env.state().previous_actions  # all actions taken

    final_info = result.info if step > 0 else {}
    episode_summary = final_info.get("episode_summary", {})
    total_reward = final_info.get("total_reward", 0.0)

    print(f"[END] difficulty={difficulty.upper()} agent={agent}  "
          f"score={total_reward:.4f}  "
          f"passed={episode_summary.get('passed', False)}  "
          f"steps={step}  "
          f"elapsed={elapsed:.1f}s "
          f"breakdown={json.dumps(episode_summary.get('breakdown', {}))}")

    return {
        "difficulty": difficulty,
        "score": total_reward,
        "passed": episode_summary.get("passed", False),
        "steps": step,
        "elapsed_seconds": round(elapsed, 2),
        "breakdown": episode_summary.get("breakdown", {}),
    }


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="MediRoute OpenEnv — Baseline Inference")
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard", "all"],
        default="all",
        help="Which task(s) to run (default: all)",
    )
    parser.add_argument(
        "--agent",
        choices=["llm", "rules"],
        default="llm",
        help="Agent policy: llm (OpenAI-compatible) or rules (offline deterministic baseline).",
    )
    args = parser.parse_args()

    # Keep output machine-parseable: rely on [START]/[STEP]/[END] markers.

    client: Optional[OpenAI] = None
    if args.agent == "llm":
        try:
            from openai import OpenAI as OpenAIClient  # type: ignore
        except ImportError:
            print("[ERROR] openai package not found. Install it or run with: --agent rules")
            sys.exit(1)
        client = OpenAIClient(api_key=API_KEY, base_url=API_BASE_URL)

    difficulties = ALL_DIFFICULTIES if args.difficulty == "all" else [args.difficulty]
    results = []

    for diff in difficulties:
        result = run_episode(client, diff, agent=args.agent)
        results.append(result)

    # ── Final leaderboard ─────────────────────────────────────────────────────
    avg_score = sum(r["score"] for r in results) / len(results)

    # Emit one final [END] summary line for strict log parsers.
    print(f"[END] summary average_score={avg_score:.4f} results={json.dumps(results)}")


if __name__ == "__main__":
    main()
