from __future__ import annotations

from typing import List, Literal, Optional
import os
import httpx

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .ai import analyze as ai_analyze
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    AppointmentCreateRequest,
    AppointmentCreateResponse,
    HospitalsResponse,
    SosRequest,
    SosResponse,
)
from .store import DB, compute_demo_eta_seconds, generate_sos_tracking_code, sort_hospitals, hospitals_for_location


app = FastAPI(title="LifeLine AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(default=[])) -> dict:
    """
    Demo-safe upload endpoint:
    - accepts PDFs/images/prescriptions
    - does not persist to disk by default (to keep MVP simple)
    - returns filenames so the analyze endpoint can reference them
    """
    names = []
    for f in files:
        # Read a small amount to validate stream; don't store.
        _ = await f.read(1024)
        names.append(f.filename or "upload")
    return {"uploaded_files": names}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(symptoms: str = Form(...), location: str = Form(...), uploaded_files: str = Form("[]")) -> AnalyzeResponse:
    """
    Triage analysis endpoint.
    Uses an AI abstraction layer:
    - LLM mode if env vars set (OPENAI_API_KEY + optional API_BASE_URL/MODEL_NAME)
    - otherwise deterministic heuristic mode for instant demos
    """
    import json

    try:
        files = json.loads(uploaded_files)
        if not isinstance(files, list):
            files = []
    except Exception:
        files = []

    req = AnalyzeRequest(symptoms=symptoms, location=location, uploaded_files=[str(x) for x in files][:10])
    return await ai_analyze(req)


@app.get("/hospitals", response_model=HospitalsResponse)
def hospitals(
    location: str,
    sort: Literal["best_rated", "closest", "fastest_route"] = "closest",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> HospitalsResponse:
    # If client provides coordinates, adjust distances/etas based on that location
    if lat is not None and lng is not None:
        hs = sort_hospitals(hospitals_for_location(DB.hospitals, lat, lng), sort)
    else:
        hs = sort_hospitals(DB.hospitals, sort)
    return HospitalsResponse(location=location, sort=sort, hospitals=hs)


@app.post("/appointments", response_model=AppointmentCreateResponse)
def create_appointment(req: AppointmentCreateRequest) -> AppointmentCreateResponse:
    appt = DB.create_appointment(req)
    return AppointmentCreateResponse(appointment=appt)


@app.get("/appointments")
def list_appointments() -> dict:
    return {"appointments": [a.model_dump() for a in DB.list_appointments()]}


@app.post("/sos", response_model=SosResponse)
def sos(req: SosRequest) -> SosResponse:
    # Always pick the closest hospital for SOS demo.
    hs = sort_hospitals(DB.hospitals, "fastest_route")
    nearest = hs[0]
    eta_seconds = compute_demo_eta_seconds(nearest)
    return SosResponse(
        nearest_hospital=nearest,
        eta_seconds=eta_seconds,
        tracking_code=generate_sos_tracking_code(),
        message="Ambulance dispatched. Stay calm—help is on the way.",
        meta={"location": req.location, "symptoms": req.symptoms or ""},
    )


@app.get("/reverse-geocode")
def reverse_geocode(lat: float, lng: float) -> dict:
    """
    Server-side reverse geocoding endpoint.
    Uses provider configured by GEOCODER_PROVIDER (default: nominatim).
    Returns JSON: { display_name, lat, lng } or raises HTTPException on error.
    """
    provider = os.getenv("GEOCODER_PROVIDER", "nominatim")
    try:
        if provider == "nominatim":
            url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lng}"
            headers = {"User-Agent": "LifeLineAI-Demo/1.0"}
            r = httpx.get(url, headers=headers, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            return {"display_name": data.get("display_name", ""), "lat": lat, "lng": lng}
        else:
            # Unsupported provider configured
            from fastapi import HTTPException

            raise HTTPException(status_code=501, detail=f"Geocoder provider '{provider}' not implemented")
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=502, detail=f"Reverse geocode failed: {e}")

