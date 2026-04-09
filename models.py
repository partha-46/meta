"""
models.py — Typed Pydantic models for the MediRoute OpenEnv environment.

These models define the complete interface contract for the AI agent:
 - Observation: what the agent perceives at each step
 - Action:       what the agent can do
 - StepResult:  what the environment returns after each action
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
#  Observation
# ─────────────────────────────────────────────
class Observation(BaseModel):
    """Everything the agent can see about the current patient and environment."""

    symptoms: str = Field(
        ..., description="Free-text description of the patient's chief complaints."
    )
    lab_report_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key lab / vital results (e.g. {'bp': '160/100', 'spo2': '98%'}).",
    )
    severity_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Numeric severity 0 (trivial) → 1 (life-threatening). "
        "Starts at 0; updated by the environment after analysis.",
    )
    location: str = Field(..., description="Patient's current geographic area/district.")
    nearby_hospitals: List[str] = Field(
        default_factory=list,
        description="Ordered list of hospitals reachable from the patient's location.",
    )
    available_specialists: List[str] = Field(
        default_factory=list,
        description="Specialists currently on-call or available for consultation.",
    )
    previous_actions: List[str] = Field(
        default_factory=list,
        description="Ordered list of actions already taken in this episode "
        "(format: '<action_type>:<target>').",
    )

    class Config:
        validate_assignment = True


# ─────────────────────────────────────────────
#  Action
# ─────────────────────────────────────────────
VALID_ACTION_TYPES = {
    "analyze_symptoms",
    "request_more_info",
    "recommend_specialist",
    "select_hospital",
    "book_appointment",
    "call_ambulance",
    "provide_temp_guidance",
}


class Action(BaseModel):
    """A single action the agent submits to the environment."""

    action_type: str = Field(
        ...,
        description=(
            "One of: analyze_symptoms | request_more_info | recommend_specialist | "
            "select_hospital | book_appointment | call_ambulance | provide_temp_guidance"
        ),
    )
    target: Optional[str] = Field(
        None,
        description=(
            "Contextual target of the action, e.g. severity level, specialist name, "
            "hospital name, or None for actions that don't require a target."
        ),
    )

    def validate_action_type(self) -> bool:
        return self.action_type in VALID_ACTION_TYPES

    def as_key(self) -> str:
        """Canonical string representation used for deduplication."""
        return f"{self.action_type}:{self.target}"


# ─────────────────────────────────────────────
#  StepResult  (returned by env.step())
# ─────────────────────────────────────────────
class StepResult(BaseModel):
    """The structured return value from MediRouteEnv.step()."""

    observation: Observation = Field(..., description="Updated environment observation.")
    reward: float = Field(
        ...,
        description="Incremental reward earned by this single action (can be negative).",
    )
    done: bool = Field(
        ..., description="Whether the episode has terminated after this action."
    )
    info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic extras: total_reward, raw_step_reward, error messages.",
    )
