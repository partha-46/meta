from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


UrgencyLevel = Literal["low", "medium", "high", "emergency"]


class AnalyzeRequest(BaseModel):
    symptoms: str = Field(..., min_length=3, max_length=4000)
    location: str = Field(..., min_length=2, max_length=200)
    # Filenames only; actual file bytes are uploaded separately.
    uploaded_files: List[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    possible_condition: str
    urgency: UrgencyLevel
    recommended_department: str
    temporary_precautions: List[str]
    recommended_next_step: str
    disclaimer: str
    confidence_note: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    model_provider: str = "heuristic"
    model_name: str = "rule-based"


class Hospital(BaseModel):
    id: str
    name: str
    distance_km: float = Field(..., ge=0.0)
    eta_minutes: int = Field(..., ge=1, le=180)
    rating: float = Field(..., ge=0.0, le=5.0)
    specialties: List[str] = Field(default_factory=list)
    availability: Literal["open", "limited", "busy"] = "open"
    address: str
    phone: str
    lat: float
    lng: float


class HospitalsResponse(BaseModel):
    location: str
    sort: Literal["best_rated", "closest", "fastest_route"] = "closest"
    hospitals: List[Hospital]


class AppointmentCreateRequest(BaseModel):
    hospital_id: str
    department: str
    doctor: str
    time_slot: str
    patient_name: str = Field(..., min_length=2, max_length=120)
    patient_phone: str = Field(..., min_length=6, max_length=40)


class Appointment(BaseModel):
    id: str
    hospital_id: str
    hospital_name: str
    department: str
    doctor: str
    time_slot: str
    patient_name: str
    patient_phone: str
    status: Literal["confirmed", "cancelled"] = "confirmed"
    created_at_iso: str


class AppointmentCreateResponse(BaseModel):
    appointment: Appointment


class SosRequest(BaseModel):
    location: str
    symptoms: Optional[str] = None


class SosResponse(BaseModel):
    status: Literal["ambulance_dispatched"] = "ambulance_dispatched"
    nearest_hospital: Hospital
    eta_seconds: int = Field(..., ge=30, le=3600)
    tracking_code: str
    message: str
    meta: Dict[str, Any] = Field(default_factory=dict)

