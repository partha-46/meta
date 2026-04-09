from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from .models import Appointment, AppointmentCreateRequest, Hospital


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_hospitals() -> List[Hospital]:
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "data", "hospitals.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Hospital(**h) for h in raw]


def sort_hospitals(hospitals: List[Hospital], sort: Literal["best_rated", "closest", "fastest_route"]) -> List[Hospital]:
    if sort == "best_rated":
        return sorted(hospitals, key=lambda h: (-h.rating, h.eta_minutes, h.distance_km))
    if sort == "fastest_route":
        return sorted(hospitals, key=lambda h: (h.eta_minutes, h.distance_km, -h.rating))
    return sorted(hospitals, key=lambda h: (h.distance_km, h.eta_minutes, -h.rating))


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance between two points in kilometers."""
    from math import radians, sin, cos, asin, sqrt

    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371.0 * c


def hospitals_for_location(hospitals: List[Hospital], lat: float, lng: float) -> List[Hospital]:
    """
    Return a new list of Hospital objects with distance_km and eta_minutes adjusted
    according to the provided lat/lng (user location). This is used for demo proximity
    sorting when the client provides coordinates.
    """
    new: List[Hospital] = []
    for h in hospitals:
        dist = _haversine_km(lat, lng, h.lat, h.lng)
        # Estimate ETA: assume average driving speed ~40 km/h -> minutes = dist/40*60 = dist*1.5
        eta = max(3, int(round(dist * 1.5)))
        # Create a shallow copy with updated fields
        nh = Hospital(**{**h.model_dump(), "distance_km": round(dist, 2), "eta_minutes": eta})
        new.append(nh)
    return new


class InMemoryDB:
    def __init__(self) -> None:
        self._appointments: Dict[str, Appointment] = {}
        self._hospitals = load_hospitals()

    @property
    def hospitals(self) -> List[Hospital]:
        return self._hospitals

    def get_hospital(self, hospital_id: str) -> Optional[Hospital]:
        for h in self._hospitals:
            if h.id == hospital_id:
                return h
        return None

    def create_appointment(self, req: AppointmentCreateRequest) -> Appointment:
        hosp = self.get_hospital(req.hospital_id)
        hospital_name = hosp.name if hosp else "Unknown Hospital"
        appt = Appointment(
            id="appt_" + uuid.uuid4().hex[:12],
            hospital_id=req.hospital_id,
            hospital_name=hospital_name,
            department=req.department,
            doctor=req.doctor,
            time_slot=req.time_slot,
            patient_name=req.patient_name,
            patient_phone=req.patient_phone,
            status="confirmed",
            created_at_iso=_now_iso(),
        )
        self._appointments[appt.id] = appt
        return appt

    def list_appointments(self) -> List[Appointment]:
        return sorted(self._appointments.values(), key=lambda a: a.created_at_iso, reverse=True)


DB = InMemoryDB()


def generate_sos_tracking_code() -> str:
    return "SOS-" + uuid.uuid4().hex[:8].upper()


def compute_demo_eta_seconds(hospital: Hospital) -> int:
    # Convert minutes to seconds with a small deterministic variation.
    jitter = int((hospital.distance_km * 7) % 20)
    return max(60, hospital.eta_minutes * 60 + jitter)

