"""
graders.py — Reward shaping logic for MediRoute OpenEnv.

Each action is evaluated against the ground-truth task expectations.
Rewards are incremental per-step values; the environment accumulates and
clamps the episode total to [0.0, 1.0].

Reward table
─────────────────────────────────────────────────────────────────
 Correct severity classification (analyze_symptoms)   +0.30
 Correct specialist recommendation                    +0.30
 Correct hospital selection                           +0.20
 Successful appointment booking (non-emergency)       +0.20
 Correct emergency escalation (call_ambulance)        +0.50
 Wrong department / specialist                        -0.20
 Unnecessary loop / duplicate action                  -0.30
 Calling ambulance on non-emergency                   -0.30
 Booking appointment in emergency case                -0.30
─────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from typing import Any, Dict, List

from models import Action


# ─────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────

def _is_duplicate(action: Action, previous_actions: List[str]) -> bool:
    return action.as_key() in previous_actions


# ─────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────

def grade_step(
    task: Dict[str, Any],
    action: Action,
    previous_actions: List[str],
) -> float:
    """
    Compute the incremental reward for a single action taken in *task*.

    Args:
        task:             The full task dict as returned by tasks.get_task().
        action:           The Action the agent wants to execute.
        previous_actions: Actions already taken this episode (as 'type:target' strings).

    Returns:
        A float reward value (can be negative; clamping is done in the environment).
    """

    # ── Duplicate penalty ────────────────────────────────────────────────────
    if _is_duplicate(action, previous_actions):
        return -0.30

    action_type = action.action_type
    target = (action.target or "").strip()

    # ── analyze_symptoms ─────────────────────────────────────────────────────
    if action_type == "analyze_symptoms":
        if target.lower() == task["expected_severity"].lower():
            return 0.30
        else:
            return -0.10   # Incorrect severity assessment

    # ── request_more_info ────────────────────────────────────────────────────
    elif action_type == "request_more_info":
        # Neutral in most cases; mild reward only if no prior analysis done
        analyzed = any(a.startswith("analyze_symptoms") for a in previous_actions)
        return 0.05 if not analyzed else -0.05

    # ── recommend_specialist ─────────────────────────────────────────────────
    elif action_type == "recommend_specialist":
        if target == task["expected_specialist"]:
            return 0.30
        else:
            return -0.20   # Wrong department

    # ── select_hospital ──────────────────────────────────────────────────────
    elif action_type == "select_hospital":
        if target == task["expected_hospital"]:
            return 0.20
        elif target in task["nearby_hospitals"]:
            return 0.05    # Nearby but not optimal
        else:
            return -0.10   # Unknown / unreachable hospital

    # ── book_appointment ─────────────────────────────────────────────────────
    elif action_type == "book_appointment":
        if task["requires_ambulance"]:
            # Trying to book appointment in a life-threatening emergency is wrong
            return -0.30
        return 0.20

    # ── call_ambulance ───────────────────────────────────────────────────────
    elif action_type == "call_ambulance":
        if task["requires_ambulance"]:
            return 0.50    # Correct emergency escalation
        else:
            return -0.30   # Unnecessary ambulance dispatch

    # ── provide_temp_guidance ─────────────────────────────────────────────────
    elif action_type == "provide_temp_guidance":
        # Acceptable as a closing action for non-emergencies
        if not task["requires_ambulance"]:
            return 0.10
        else:
            return -0.10   # Not enough for a critical patient

    # ── Unknown action ────────────────────────────────────────────────────────
    return -0.10


def grade_episode(
    task: Dict[str, Any],
    all_actions: List[str],
    final_total_reward: float,
) -> Dict[str, Any]:
    """
    Produce a final episode summary / score report.

    Args:
        task:               Task dict.
        all_actions:        Full list of action keys taken during the episode.
        final_total_reward: Accumulated clamped reward from the environment.

    Returns:
        A dict with score, pass/fail, and diagnostic breakdown.
    """
    score = round(final_total_reward, 4)
    passed = score >= 0.5

    breakdown = {
        "severity_classified": any(
            a.startswith(f"analyze_symptoms:{task['expected_severity']}")
            for a in all_actions
        ),
        "correct_specialist": any(
            a.startswith(f"recommend_specialist:{task['expected_specialist']}")
            for a in all_actions
        ),
        "correct_hospital": any(
            a.startswith(f"select_hospital:{task['expected_hospital']}")
            for a in all_actions
        ),
        "ambulance_called": any(a.startswith("call_ambulance") for a in all_actions),
        "appointment_booked": any(a.startswith("book_appointment") for a in all_actions),
    }

    return {
        "score": score,
        "passed": passed,
        "difficulty": task["difficulty"],
        "total_steps": len(all_actions),
        "breakdown": breakdown,
    }
