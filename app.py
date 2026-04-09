"""
app.py — Interactive entrypoint for MediRoute OpenEnv.

Run this script for a quick interactive session with the environment:
    python app.py --difficulty easy
    python app.py --difficulty medium
    python app.py --difficulty hard

The script drives a simple REPL loop so you can manually test the environment
without running the full AI inference pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys

from environment import MediRouteEnv
from models import Action
from tasks import list_tasks


def print_obs(obs) -> None:
    sep = "─" * 60
    print(sep)
    print(f"  📍 Location       : {obs.location}")
    print(f"  🤒 Symptoms       : {obs.symptoms}")
    print(f"  🔬 Labs           : {json.dumps(obs.lab_report_summary, indent=4)}")
    print(f"  ⚡ Severity score : {obs.severity_score:.2f}")
    print(f"  🏥 Hospitals      : {obs.nearby_hospitals}")
    print(f"  👨‍⚕️ Specialists    : {obs.available_specialists}")
    print(f"  📋 Past actions   : {obs.previous_actions or '(none)'}")
    print(sep)


def repl(difficulty: str) -> None:
    env = MediRouteEnv()
    obs = env.reset(difficulty=difficulty)

    print(f"\n🏥  MediRoute OpenEnv — difficulty: {difficulty.upper()}")
    print_obs(obs)

    valid_types = [
        "analyze_symptoms",
        "request_more_info",
        "recommend_specialist",
        "select_hospital",
        "book_appointment",
        "call_ambulance",
        "provide_temp_guidance",
    ]
    print("Valid action types:", ", ".join(valid_types))
    print("Type  'quit' to exit.\n")

    while True:
        raw = input("action_type [target]: ").strip()
        if raw.lower() in {"quit", "exit", "q"}:
            break

        parts = raw.split(maxsplit=1)
        action_type = parts[0]
        target = parts[1] if len(parts) > 1 else None

        action = Action(action_type=action_type, target=target)
        result = env.step(action)

        reward_sign = "+" if result.reward >= 0 else ""
        print(f"\n  Reward : {reward_sign}{result.reward:.2f}")
        print(f"  Done   : {result.done}")
        print(f"  Total  : {result.info.get('total_reward', 0):.2f}")

        if result.done:
            summary = result.info.get("episode_summary", {})
            print("\n🎯  Episode complete!")
            print(json.dumps(summary, indent=4))
            break
        else:
            print_obs(result.observation)


def main() -> None:
    parser = argparse.ArgumentParser(description="MediRoute OpenEnv interactive REPL")
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="easy",
        help="Task difficulty level (default: easy)",
    )
    parser.add_argument("--list-tasks", action="store_true", help="List available tasks and exit")

    args = parser.parse_args()

    if args.list_tasks:
        print("\nAvailable Tasks:\n")
        for diff, desc in list_tasks().items():
            print(f"  [{diff.upper():6}]  {desc}")
        sys.exit(0)

    repl(args.difficulty)


if __name__ == "__main__":
    main()
