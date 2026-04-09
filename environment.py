"""
environment.py — Core MediRoute OpenEnv environment.

This module implements the standard OpenEnv interface:
    env.reset(difficulty) → Observation
    env.step(action)      → StepResult
    env.state()           → Observation

The environment is fully deterministic given the same task; no randomness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from graders import grade_episode, grade_step
from models import Action, Observation, StepResult
from tasks import get_task


@dataclass(frozen=True)
class DoneReason:
    code: str
    message: str


class MediRouteEnv:
    """
    Medical Triage and Hospital Routing simulation environment.

    Follows the OpenEnv specification:
      ┌──────────────────────────────────────────────────────────┐
      │  reset(difficulty)  →  Observation                       │
      │  step(action)       →  StepResult(obs, reward, done, info)│
      │  state()            →  Observation (read-only snapshot)  │
      └──────────────────────────────────────────────────────────┘
    """

    # Class-level metadata (used by openenv.yaml / registry)
    ENV_ID: str = "mediroute-openenv-v1"
    VERSION: str = "1.0.0"

    def __init__(self) -> None:
        self._task: Dict[str, Any] = {}
        self._obs: Observation | None = None
        self._total_reward: float = 0.0
        self._done: bool = False
        self._step_count: int = 0
        self._done_reason: Optional[DoneReason] = None

    # ─────────────────────────────────────────────
    #  OpenEnv Interface
    # ─────────────────────────────────────────────

    def reset(self, difficulty: str = "easy") -> Observation:
        """
        Initialise (or re-initialise) the environment for a new episode.

        Args:
            difficulty: One of 'easy', 'medium', 'hard'.

        Returns:
            The initial Observation the agent should act upon.
        """
        self._task = get_task(difficulty)
        self._total_reward = 0.0
        self._done = False
        self._done_reason = None
        self._step_count = 0

        self._obs = Observation(
            symptoms=self._task["symptoms"],
            lab_report_summary=self._task["lab_report_summary"],
            severity_score=self._task["severity_score"],
            location=self._task["location"],
            nearby_hospitals=self._task["nearby_hospitals"],
            available_specialists=self._task["available_specialists"],
            previous_actions=[],
        )
        return self._obs

    def step(self, action: Action) -> StepResult:
        """
        Advance the environment by one action.

        Args:
            action: A typed Action submitted by the agent.

        Returns:
            StepResult with updated observation, step reward, done flag, and info.
        """
        if self._obs is None:
            raise RuntimeError("Environment not initialised. Call reset() first.")

        if self._done:
            return StepResult(
                observation=self._obs,
                reward=0.0,
                done=True,
                info={
                    "warning": "Episode is already done; no further steps are accepted.",
                    "total_reward": self._total_reward,
                    "done_reason": (self._done_reason.code if self._done_reason else "done"),
                },
            )

        # ── Validate action type ───────────────────────────────────────────────
        if not action.validate_action_type():
            return StepResult(
                observation=self._obs,
                reward=-0.10,
                done=False,
                info={
                    "error": f"Unknown action_type '{action.action_type}'.",
                    "total_reward": self._total_reward,
                },
            )

        # ── Basic action schema validation (deterministic, non-throwing) ───────
        invalid_reason, target_norm = self._validate_action_semantics(action)
        if invalid_reason:
            # Do not mutate state for invalid semantic actions; keep episode running.
            return StepResult(
                observation=self._obs,
                reward=-0.10,
                done=False,
                info={
                    "error": invalid_reason,
                    "total_reward": self._total_reward,
                },
            )

        # ── Compute incremental reward ────────────────────────────────────────
        raw_reward = grade_step(
            task=self._task,
            action=action,
            previous_actions=self._obs.previous_actions,
        )

        # ── Accumulate and clamp total reward to [0, 1] ───────────────────────
        new_total = max(0.0, min(1.0, self._total_reward + raw_reward))
        incremental_reward = new_total - self._total_reward
        self._total_reward = new_total

        # ── Update observation: record action, update severity_score ──────────
        self._obs.previous_actions.append(action.as_key())
        self._step_count += 1

        # Reflect severity classification if agent analysed symptoms
        if action.action_type == "analyze_symptoms" and target_norm:
            severity_map = {"low": 0.2, "moderate": 0.5, "high": 0.75, "critical": 0.95}
            # If an unknown target somehow slips through, do not overwrite severity.
            if target_norm in severity_map:
                self._obs.severity_score = severity_map[target_norm]

        # ── Determine if episode terminates ───────────────────────────────────
        terminal_actions = self._task.get("terminal_actions", {"book_appointment", "call_ambulance"})
        max_steps = self._task.get("max_steps", 8)

        if action.action_type in terminal_actions:
            self._done = True
            self._done_reason = DoneReason(
                code="terminal_action",
                message=f"Episode ended by terminal action: {action.action_type}.",
            )
        elif self._step_count >= max_steps:
            self._done = True
            self._done_reason = DoneReason(
                code="max_steps",
                message=f"Episode ended after reaching max_steps={max_steps}.",
            )

        # ── Build info payload ────────────────────────────────────────────────
        info: Dict[str, Any] = {
            "step": self._step_count,
            "raw_step_reward": raw_reward,
            "total_reward": self._total_reward,
            "done": self._done,
            "done_reason": (self._done_reason.code if self._done_reason else None),
        }

        if self._done:
            info["episode_summary"] = grade_episode(
                task=self._task,
                all_actions=self._obs.previous_actions,
                final_total_reward=self._total_reward,
            )

        return StepResult(
            observation=self._obs,
            reward=incremental_reward,
            done=self._done,
            info=info,
        )

    def state(self) -> Observation:
        """Return the current observation without advancing the environment."""
        if self._obs is None:
            raise RuntimeError("Environment not initialised. Call reset() first.")
        return self._obs

    # ─────────────────────────────────────────────
    #  Validation helpers
    # ─────────────────────────────────────────────

    def _validate_action_semantics(self, action: Action) -> Tuple[Optional[str], Optional[str]]:
        """
        Validate action semantics in a deterministic, non-throwing way.

        Returns:
            (error_message_or_none, normalized_target_or_none)
        """
        action_type = action.action_type
        target = (action.target or "").strip()
        target_norm = target.lower() if target else None

        # Target requirements
        if action_type == "analyze_symptoms":
            if not target_norm:
                return "analyze_symptoms requires a target severity: low|moderate|high|critical.", None
            if target_norm not in {"low", "moderate", "high", "critical"}:
                return "Invalid severity target for analyze_symptoms (use low|moderate|high|critical).", None
            return None, target_norm

        if action_type in {"recommend_specialist", "select_hospital"} and not target:
            return f"{action_type} requires a non-empty target.", None

        # Loop prevention / stalling guardrails (lightweight, deterministic)
        # Excessive 'request_more_info' stalls the episode without progress.
        if action_type == "request_more_info":
            recent = self._obs.previous_actions[-3:] if self._obs else []
            if sum(1 for a in recent if a.startswith("request_more_info:")) >= 2:
                # Not invalid, but strongly discouraged: let grader penalize via duplicates/negative.
                return None, target_norm

        return None, target_norm
