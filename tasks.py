"""
tasks.py — Deterministic task definitions for MediRoute OpenEnv.

Each task is a fully specified medical scenario with:
  - Initial state (symptoms, labs, location, nearby hospitals, specialists)
  - Ground-truth expectations used by the grader
  - Difficulty metadata

Tasks are purely data; no side-effects happen here.
"""

from __future__ import annotations

from typing import Any, Dict

# ─────────────────────────────────────────────
#  Task Registry
# ─────────────────────────────────────────────

TASKS: Dict[str, Dict[str, Any]] = {
    # ── EASY ──────────────────────────────────────────────────────────────────
    "easy": {
        "difficulty": "easy",
        "description": "Mild illness — fever and sore throat.",
        "symptoms": "Patient reports fever (101.5 °F) and sore throat for 2 days.",
        "lab_report_summary": {
            "temperature_f": 101.5,
            "strep_rapid_test": "positive",
            "wbc": "11,200 / µL (mildly elevated)",
        },
        # Initial severity — agent must classify this
        "severity_score": 0.0,
        "location": "Downtown",
        "nearby_hospitals": [
            "City Clinic",
            "Downtown Medical Center",
            "Northside Hospital",
        ],
        "available_specialists": [
            "General Physician",
            "ENT Specialist",
            "Cardiologist",
            "Emergency Doctor",
        ],
        # Ground-truth answers for graders
        "expected_severity": "low",
        "expected_specialist": "General Physician",
        "expected_hospital": "City Clinic",
        "requires_ambulance": False,
        "terminal_actions": {"book_appointment", "provide_temp_guidance"},
        "max_steps": 6,
    },

    # ── MEDIUM ────────────────────────────────────────────────────────────────
    "medium": {
        "difficulty": "medium",
        "description": "Cardiology case — chest pain, high BP, ECG abnormality.",
        "symptoms": (
            "55-year-old male with crushing chest pain radiating to left arm, "
            "persistent for 30 minutes. Hypertension history."
        ),
        "lab_report_summary": {
            "blood_pressure": "165/105 mmHg",
            "ecg_finding": "ST-segment elevation in leads II, III, aVF",
            "troponin_i": "0.9 ng/mL (elevated)",
            "heart_rate": "102 bpm",
        },
        "severity_score": 0.0,
        "location": "Westside",
        "nearby_hospitals": [
            "Westside Heart Center",
            "General Hospital",
            "City Clinic",
        ],
        "available_specialists": [
            "Cardiologist",
            "General Physician",
            "Emergency Doctor",
            "ENT Specialist",
        ],
        "expected_severity": "high",
        "expected_specialist": "Cardiologist",
        "expected_hospital": "Westside Heart Center",
        "requires_ambulance": False,
        "terminal_actions": {"book_appointment", "provide_temp_guidance"},
        "max_steps": 8,
    },

    # ── HARD ──────────────────────────────────────────────────────────────────
    "hard": {
        "difficulty": "hard",
        "description": "Life-threatening emergency — severe chest pain, SpO₂ crash, unresponsive.",
        "symptoms": (
            "Elderly female found unresponsive. Bystander reports sudden "
            "severe chest pain followed by collapse. Lips cyanotic."
        ),
        "lab_report_summary": {
            "spo2": "78 % (critical)",
            "pulse": "thready / barely palpable",
            "consciousness": "GCS 3 — unresponsive",
            "respiratory_rate": "6 breaths/min",
        },
        "severity_score": 0.0,
        "location": "Northside",
        "nearby_hospitals": [
            "Northside Hospital (ICU)",
            "General Hospital",
            "Westside Heart Center",
        ],
        "available_specialists": [
            "Emergency Doctor",
            "Cardiologist",
            "General Physician",
        ],
        "expected_severity": "critical",
        "expected_specialist": "Emergency Doctor",
        "expected_hospital": "Northside Hospital (ICU)",
        "requires_ambulance": True,
        "terminal_actions": {"call_ambulance", "book_appointment", "provide_temp_guidance"},
        "max_steps": 6,
    },
}


def get_task(difficulty: str) -> Dict[str, Any]:
    """Return a defensive copy of the task definition for the given difficulty."""
    key = difficulty.lower().strip()
    if key not in TASKS:
        raise ValueError(
            f"Unknown difficulty '{difficulty}'. "
            f"Available options: {sorted(TASKS.keys())}"
        )
    # Deep copy primitive fields; lists/dicts are re-created automatically
    import copy
    return copy.deepcopy(TASKS[key])


def list_tasks() -> Dict[str, str]:
    """Return a {difficulty: description} summary for logging / display."""
    return {k: v["description"] for k, v in TASKS.items()}
