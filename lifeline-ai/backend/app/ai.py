from __future__ import annotations

import os
import re
from typing import Optional

import httpx

from .hf_torch import classify_with_hf_pytorch
from .models import AnalyzeRequest, AnalyzeResponse

# Optional local embedding resources (cached)
_emb_model = None
_emb_documents = None
_emb_doc_embeddings = None

DISCLAIMER = (
    "This is an AI-assisted triage suggestion, not a medical diagnosis. "
    "If symptoms are severe or worsening, seek in-person medical care immediately."
)


def _heuristic_triage(req: AnalyzeRequest) -> AnalyzeResponse:
    s = req.symptoms.lower()

    emergency_signals = any(
        kw in s
        for kw in [
            "unresponsive",
            "faint",
            "collapsed",
            "blue lips",
            "cyanotic",
            "severe bleeding",
            "cannot breathe",
            "no breathing",
            "seizure",
        ]
    )
    cardiac_signals = any(
        kw in s
        for kw in [
            "chest pain",
            "shortness of breath",
            "pain radiating",
            "left arm",
            "tightness",
            "pressure in chest",
        ]
    )
    infection_signals = any(kw in s for kw in ["fever", "sore throat", "cough", "chills"])

    if emergency_signals:
        return AnalyzeResponse(
            possible_condition="Possible emergency event (airway/breathing/circulation concern)",
            urgency="emergency",
            recommended_department="Emergency",
            temporary_precautions=[
                "Call local emergency services immediately.",
                "If trained, start basic life support and keep the airway open.",
                "Do not give food or drink if the person is unconscious.",
            ],
            recommended_next_step="Use SOS to request an ambulance now. Go to the nearest emergency-capable hospital.",
            disclaimer=DISCLAIMER,
            confidence_note="Heuristic demo mode (offline).",
            confidence_score=0.72,
            model_provider="heuristic",
            model_name="rules-v1",
        )

    if cardiac_signals:
        return AnalyzeResponse(
            possible_condition="Possible cardiac concern",
            urgency="high",
            recommended_department="Cardiology",
            temporary_precautions=[
                "Stop exertion and sit upright.",
                "If symptoms worsen, do not drive yourself—use ambulance support.",
                "If prescribed by a clinician previously, follow your emergency plan.",
            ],
            recommended_next_step="Visit the nearest hospital within 30 minutes; prefer a cardiac-capable center.",
            disclaimer=DISCLAIMER,
            confidence_note="Heuristic demo mode (offline).",
            confidence_score=0.76,
            model_provider="heuristic",
            model_name="rules-v1",
        )

    if infection_signals:
        return AnalyzeResponse(
            possible_condition="Possible infection / flu-like illness",
            urgency="medium",
            recommended_department="General Medicine",
            temporary_precautions=[
                "Hydrate and rest.",
                "Monitor temperature and breathing.",
                "Seek urgent care if severe shortness of breath, confusion, or persistent high fever occurs.",
            ],
            recommended_next_step="Book an appointment with a general physician within 24–48 hours.",
            disclaimer=DISCLAIMER,
            confidence_note="Heuristic demo mode (offline).",
            confidence_score=0.68,
            model_provider="heuristic",
            model_name="rules-v1",
        )

    return AnalyzeResponse(
        possible_condition="Possible non-specific concern",
        urgency="low",
        recommended_department="General Medicine",
        temporary_precautions=[
            "Monitor symptoms and avoid triggers.",
            "Write down symptom timeline and any medications taken.",
        ],
        recommended_next_step="If symptoms persist, book a routine appointment.",
        disclaimer=DISCLAIMER,
        confidence_note="Heuristic demo mode (offline).",
        confidence_score=0.55,
        model_provider="heuristic",
        model_name="rules-v1",
    )


def _hf_pytorch_triage(req: AnalyzeRequest) -> Optional[AnalyzeResponse]:
    """
    Sponsor-facing inference path:
    Uses a Hugging Face transformer pipeline running on PyTorch.
    Returns None on any runtime/dependency issue to preserve resilient fallback.
    """
    try:
        pred = classify_with_hf_pytorch(req.symptoms)
    except Exception:
        return None

    dept = pred.department
    urgency = pred.urgency

    if urgency == "emergency":
        possible = "Possible life-threatening emergency"
        next_step = "Use SOS now and proceed to the nearest emergency-capable hospital."
        precautions = [
            "Call emergency services immediately.",
            "Keep the patient still and monitor breathing.",
            "Do not delay for non-essential procedures.",
        ]
    elif urgency == "high":
        possible = "Possible acute clinical concern requiring urgent care"
        next_step = "Visit a hospital within 30 minutes; prioritize facilities with critical care support."
        precautions = [
            "Avoid physical exertion.",
            "Keep communication available and avoid driving alone if worsening.",
            "Prepare prior records/medication list for triage.",
        ]
    elif urgency == "medium":
        possible = "Possible moderate clinical issue"
        next_step = "Book an appointment soon and monitor changes over the next 24 hours."
        precautions = [
            "Hydrate and rest.",
            "Track symptom progression.",
            "Escalate to urgent care if worsening rapidly.",
        ]
    else:
        possible = "Possible mild clinical issue"
        next_step = "Monitor symptoms and schedule a routine consultation if persistent."
        precautions = [
            "Continue observation and rest.",
            "Record onset, triggers, and duration of symptoms.",
        ]

    return AnalyzeResponse(
        possible_condition=possible,
        urgency=urgency,  # type: ignore[arg-type]
        recommended_department=dept,
        temporary_precautions=precautions,
        recommended_next_step=next_step,
        disclaimer=DISCLAIMER,
        confidence_note=f"Hugging Face transformer inference via PyTorch ({pred.model_name}).",
        confidence_score=pred.confidence,
        model_provider=pred.provider,
        model_name=pred.model_name,
    )


def _local_embeddings_triage(req: AnalyzeRequest) -> Optional[AnalyzeResponse]:
    """
    Use a local sentence-transformers model to find the closest matching
    condition from a small medical dataset (`medical_data.json`) located
    at the repository root (meta/medical_data.json). This is a best-effort
    offline fallback and returns None on any error to preserve existing
    fallback behavior.
    """
    global _emb_model, _emb_documents, _emb_doc_embeddings
    try:
        from sentence_transformers import SentenceTransformer, util
        import json
        import os
    except Exception:
        return None

    try:
        # Lazy-load model and document embeddings to avoid repeated expensive work
        if _emb_model is None:
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/embeddinggemma-300m-medical")
            _emb_model = SentenceTransformer(model_name)

        if _emb_documents is None or _emb_doc_embeddings is None:
            # medical_data.json is located at repo root
            repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            data_path = os.path.join(repo_root, "medical_data.json")
            if not os.path.exists(data_path):
                return None
            with open(data_path, "r") as fh:
                medical_data = json.load(fh)

            # Build searchable text in the same format as test.py
            documents = [
                f"{item['condition']}. Symptoms: {item['symptoms']}. Causes: {item['causes']}. Precautions: {item['precautions']}. Doctor advice: {item['see_doctor']}"
                for item in medical_data
            ]

            if not documents:
                return None

            _emb_documents = medical_data
            _emb_doc_embeddings = _emb_model.encode(documents, convert_to_tensor=True)
    except Exception:
        return None

    try:
        # Encode query and compute similarity
        query_embedding = _emb_model.encode(req.symptoms, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, _emb_doc_embeddings)[0]
        best_idx = int(scores.argmax().item())
        best_score = float(scores[best_idx].item())
        best_match = _emb_documents[best_idx]
    except Exception:
        return None

    # Build a conservative AnalyzeResponse from the matched document
    possible = best_match.get("condition", "Possible concern")
    precautions = best_match.get("precautions", []) or []
    next_step = best_match.get("see_doctor", "Follow up with a clinician if concerned.")

    return AnalyzeResponse(
        possible_condition=str(possible),
        urgency=str(best_match.get("urgency", "low")),
        recommended_department=str(best_match.get("department", "General Medicine")),
        temporary_precautions=[str(x) for x in precautions][:6],
        recommended_next_step=str(next_step),
        disclaimer=DISCLAIMER,
        confidence_note="Local embeddings-based match",
        confidence_score=min(max(best_score, 0.0), 1.0),
        model_provider="local-embeddings",
        model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/embeddinggemma-300m-medical"),
    )


async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """
    AI abstraction layer:
    - If LLM env vars are set, call an OpenAI-compatible endpoint.
    - Otherwise fall back to deterministic heuristic triage (demo mode).
    """
    # 1) Hugging Face + PyTorch local pipeline (preferred sponsor path)
    if os.getenv("USE_HF_LOCAL", "1").strip() not in {"0", "false", "False"}:
        hf_result = _hf_pytorch_triage(req)
        if hf_result is not None:
            return hf_result

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1").strip()
    model = os.getenv("MODEL_NAME", "gpt-4o-mini").strip()

    if not api_key:
        # Try a local embeddings-based match before falling back to heuristics.
        if os.getenv("USE_LOCAL_EMBEDDINGS", "1").strip() not in {"0", "false", "False"}:
            emb = _local_embeddings_triage(req)
            if emb is not None:
                return emb

        return _heuristic_triage(req)

    system = (
        "You are LifeLine AI, a healthcare triage assistant. "
        "You must not provide a diagnosis. Use 'possible'/'likely' wording. "
        "Return STRICT JSON with keys: possible_condition, urgency, recommended_department, "
        "temporary_precautions (array of strings), recommended_next_step, confidence_note. "
        "Urgency must be one of: low, medium, high, emergency."
    )
    user = (
        f"Symptoms: {req.symptoms}\n"
        f"Location: {req.location}\n"
        f"Uploaded files: {req.uploaded_files}\n"
        "Respond with JSON only."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": 300,
    }

    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        text = (data["choices"][0]["message"]["content"] or "").strip()

    # Extract JSON object defensively
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return _heuristic_triage(req)
    import json

    try:
        obj = json.loads(m.group(0))
    except Exception:
        return _heuristic_triage(req)

    urgency = obj.get("urgency", "medium")
    if urgency not in {"low", "medium", "high", "emergency"}:
        urgency = "medium"

    tp = obj.get("temporary_precautions", [])
    if not isinstance(tp, list):
        tp = [str(tp)]

    return AnalyzeResponse(
        possible_condition=str(obj.get("possible_condition", "Possible concern")),
        urgency=urgency,  # type: ignore[arg-type]
        recommended_department=str(obj.get("recommended_department", "General Medicine")),
        temporary_precautions=[str(x) for x in tp][:6],
        recommended_next_step=str(obj.get("recommended_next_step", "Consider in-person care if symptoms worsen.")),
        disclaimer=DISCLAIMER,
        confidence_note=str(obj.get("confidence_note", "LLM mode")),
        confidence_score=float(obj.get("confidence_score", 0.7)),
        model_provider="openai-compatible",
        model_name=model,
    )

