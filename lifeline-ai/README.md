# LifeLine AI (Phase 2 MVP)

**LifeLine AI** is a production-style full-stack healthcare emergency assistance demo:
- symptom intake + report upload
- AI-assisted triage (possible/likely wording; not a diagnosis)
- nearby hospital finder (cards + demo map pins)
- appointment booking flow + confirmation modal
- a visually prominent **SOS button** (ambulance dispatch simulation with ETA + tracking code)

This folder is the Phase 2 MVP website built after the MediRoute OpenEnv simulation.

---

## What We Built

- **OpenEnv environment** from Phase 1 (`MediRouteEnv`) with deterministic grading.
- **3 graded tasks** (easy / medium / hard) for healthcare routing and escalation.
- **PyTorch clinical reasoning layer** in `backend/app/hf_torch.py`.
- **Hugging Face transformer inference** for symptom-to-department and urgency scoring.
- **Hospital ranking engine** (best rated / closest / fastest route) with realistic cards.
- **Emergency SOS workflow** with dispatch simulation, live ETA, and status progression.

---

## Tech stack

- **Frontend**: Next.js (App Router) + React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Pydantic
- **AI**:
  - Hugging Face Transformers pipeline (`facebook/bart-large-mnli`) via **PyTorch**
  - OpenAI-compatible fallback path
  - deterministic heuristic fallback for offline demos
- **Data**: mock hospital dataset (`backend/data/hospitals.json`)

---

## Run locally (recommended)

### 1) Backend API

```bash
cd lifeline-ai/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

Backend runs at `http://localhost:8000`.

Optional (LLM mode):

```bash
export OPENAI_API_KEY="..."
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
```

If `OPENAI_API_KEY` is **not** set, the backend uses **deterministic demo triage**.

### 2) Frontend web app

In a second terminal:

```bash
cd lifeline-ai
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## Demo flow

1. On the landing page (`/`), use a demo preset (cardiac / fever / collapse) or type symptoms manually.
2. Submit → results page (`/results`) with:
   - possible condition
   - urgency level
   - recommended department
   - temporary precautions
   - recommended next step
3. Explore hospitals (`/hospitals`) with sorting:
   - best rated
   - closest
   - fastest route
   + a demo map with pins
4. Book an appointment (`/book`) and view a confirmation modal.
5. Hit the **SOS** button (bottom-right) anytime for ambulance dispatch simulation.

---

## Configuration

Frontend:
- `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`)

Backend:
- `USE_HF_LOCAL` (default `1`, enables local Hugging Face + PyTorch inference path)
- `OPENAI_API_KEY` (enables LLM mode)
- `API_BASE_URL` (OpenAI-compatible base URL)
- `MODEL_NAME` (model id)

---

## Sponsor-aligned architecture

- `backend/app/hf_torch.py`:
  - loads a Hugging Face transformer pipeline with `framework="pt"`
  - performs symptom classification into department labels
  - performs urgency scoring into low/medium/high/emergency
  - returns confidence score and model metadata for UI display
- `backend/app/ai.py`:
  - first tries Hugging Face + PyTorch path
  - falls back to OpenAI-compatible model
  - then deterministic heuristic fallback
- `src/app/results/page.tsx`:
  - displays provider/model/confidence as a visible judge-facing proof point
  - includes live confidence progress UI while inference is running

---

## Sponsor-friendly pitch lines

- **Hugging Face**: "We run transformer-based triage classification using a Hugging Face pipeline to map symptom narratives into urgency and department recommendations."
- **PyTorch**: "Our inference path is explicitly PyTorch-backed (`framework='pt'`), giving us transparent, production-style model loading and confidence scoring."
- **Why this matters**: "This combines interpretable clinical routing with real-time emergency UX, making AI assistance actionable in under two minutes during a crisis demo."

