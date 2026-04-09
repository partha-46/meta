# MediRoute OpenEnv

**MediRoute OpenEnv** is a deterministic **healthcare triage + hospital routing** simulation environment designed for evaluating agent decision-making under realistic clinical constraints.

It models the end-to-end flow a real triage system must handle:
- interpret symptoms + vitals/labs
- assign severity (non-emergency → critical)
- route to the right specialist
- pick an appropriate nearby facility
- decide between **appointment vs ambulance escalation**

This environment is intentionally small, fully deterministic, and strongly typed so it can be used in hackathon evaluation pipelines and reproduced exactly.

---

## Why this matters (motivation + utility)

Healthcare triage is a high-stakes planning problem with:
- **multi-step reasoning** (severity → specialist → facility → action)
- **safety-critical escalation** (ambulance dispatch vs harmful delays)
- **real-world constraints** (limited specialists, nearby hospitals, and incomplete info)

MediRoute is useful for agent evaluation because it tests:
- **trajectory quality** (progressive reward shaping across steps)
- **loop avoidance** (duplicate actions and stalling are penalized)
- **robustness** (invalid actions are handled safely and deterministically)
- **policy compliance** (terminal actions and episode boundaries are enforced)

---

## Environment overview

- **Environment class**: `MediRouteEnv` in `environment.py`
- **Spec**: `openenv.yaml`
- **Typed interface**: `models.py` (Pydantic `Observation`, `Action`, `StepResult`)
- **Tasks**: `tasks.py` (`easy`, `medium`, `hard`)
- **Deterministic graders**: `graders.py` (`grade_step`, `grade_episode`)

OpenEnv interface methods:
- `reset(difficulty: str) -> Observation`
- `step(action: Action) -> StepResult` where `StepResult` contains:
  - `observation` (updated `Observation`)
  - `reward` (incremental step reward)
  - `done` (episode termination flag)
  - `info` (diagnostics incl. totals and termination reason)
- `state() -> Observation` (read-only snapshot)

---

## Tasks (real-world healthcare cases)

The tasks represent increasing clinical risk and decision complexity.

### Easy — mild illness (primary care)
- **Scenario**: fever + sore throat with positive strep test
- **Goal**: classify **low** severity, route to **General Physician**, choose an appropriate clinic, then close with appointment/guidance
- **Clinical realism**: routine outpatient triage with lab confirmation

### Medium — suspected acute coronary syndrome
- **Scenario**: crushing chest pain, hypertension, ECG ST-elevation, elevated troponin
- **Goal**: classify **high** severity, route to **Cardiologist**, select a cardiac-capable hospital, then close appropriately
- **Clinical realism**: time-sensitive cardiology routing

### Hard — critical collapse (life-threatening)
- **Scenario**: unresponsive patient with cyanosis and SpO₂ crash
- **Goal**: classify **critical** severity and **dispatch ambulance** (terminal action), avoiding unsafe appointment flows
- **Clinical realism**: emergency escalation with irreversible harm from delay

---

## Action space

Defined in `models.py` (`VALID_ACTION_TYPES`) and mirrored in `openenv.yaml`:

- `analyze_symptoms` — classify severity (target: `low|moderate|high|critical`)
- `request_more_info` — ask for missing details (target optional)
- `recommend_specialist` — choose specialist (target: a specialist name)
- `select_hospital` — choose facility (target: a hospital name)
- `book_appointment` — close non-emergencies (target optional)
- `call_ambulance` — escalate emergencies (target optional)
- `provide_temp_guidance` — short-term guidance (target optional)

---

## Observation space

`Observation` fields (see `models.py` and `openenv.yaml`):
- `symptoms: str`
- `lab_report_summary: dict`
- `severity_score: float` in `[0.0, 1.0]` (updated when severity is analyzed)
- `location: str`
- `nearby_hospitals: list[str]`
- `available_specialists: list[str]`
- `previous_actions: list[str]` (canonical `"<action_type>:<target>"`)

---
title: "MediRoute OpenEnv"
emoji: "🏥"
colorFrom: "blue"
colorTo: "purple"
sdk: python
sdk_version: "1.0"
python_version: "3.11"
app_file: app.py
pinned: false
---

# MediRoute OpenEnv

**MediRoute OpenEnv** is a deterministic **healthcare triage + hospital routing** simulation environment designed for evaluating agent decision-making under realistic clinical constraints.

It models the end-to-end flow a real triage system must handle:
- interpret symptoms + vitals/labs
- assign severity (non-emergency → critical)
- route to the right specialist
- pick an appropriate nearby facility
- decide between **appointment vs ambulance escalation**

This environment is intentionally small, fully deterministic, and strongly typed so it can be used in hackathon evaluation pipelines and reproduced exactly.

---

## Configuration

This project exposes several environment variables used at runtime. Keep sensitive keys server-side and out of client-side code (e.g., do not expose `GEOCODER_API_KEY` or `OPENAI_API_KEY` to the browser).

Important environment variables:

- `OPENAI_API_KEY` — (optional) API key for OpenAI if you use the LLM baseline or OpenAI-backed inference.
- `HF_TOKEN` — (optional) Hugging Face token for gated HF models.
- `API_BASE_URL` — (optional) override for OpenAI-compatible endpoints.
- `MODEL_NAME` — (optional) model name to use for LLM inference (default: `gpt-4o-mini` in examples).
- `USE_LOCAL_EMBEDDINGS` — (optional) set to `1`/`true` to enable sentence-transformers fallback for `analyze` when a cloud key is not present.
- `EMBEDDING_MODEL` — (optional) sentence-transformers model id (e.g., `all-MiniLM-L6-v2`) used by local embeddings fallback.
- `GEOCODER_PROVIDER` — (optional) `nominatim` (default) or `mapbox` or `google` if implemented; the server will use this to select reverse geocoding provider.
- `GEOCODER_API_KEY` — (required if using a paid provider) API key for the chosen geocoding provider; keep this server-side and set it as an environment variable or secret.
- `NEXT_PUBLIC_API_BASE` — (frontend) base URL for the backend API; this can point to `http://localhost:8000` in development. Avoid putting secret keys in `NEXT_PUBLIC_` vars.

Example `.env` (for local development) — do NOT commit this file into git:

```env
# .env.local (example)
OPENAI_API_KEY=""
HF_TOKEN=""
USE_LOCAL_EMBEDDINGS=1
EMBEDDING_MODEL="all-MiniLM-L6-v2"
GEOCODER_PROVIDER=nominatim
# GEOCODER_API_KEY="your_mapbox_or_google_key"
NEXT_PUBLIC_API_BASE="http://localhost:8000"
```

Docker example (passing keys at runtime):

```bash
docker run --rm -e GEOCODER_PROVIDER=mapbox -e GEOCODER_API_KEY="$MAPBOX_KEY" -e OPENAI_API_KEY="$OPENAI_KEY" -p 8000:8000 mediroute-openenv:latest
```

Notes:
- Nominatim (OpenStreetMap) is supported by default for reverse geocoding but has usage limits and a usage policy — for production use consider Mapbox or Google and set `GEOCODER_API_KEY` accordingly.
- Keep API keys on the server. The frontend should call your server endpoints (e.g., `/reverse-geocode`) rather than calling external providers directly.

---

## Why this matters (motivation + utility)

Healthcare triage is a high-stakes planning problem with:
- **multi-step reasoning** (severity → specialist → facility → action)
- **safety-critical escalation** (ambulance dispatch vs harmful delays)
- **real-world constraints** (limited specialists, nearby hospitals, and incomplete info)

MediRoute is useful for agent evaluation because it tests:
- **trajectory quality** (progressive reward shaping across steps)
- **loop avoidance** (duplicate actions and stalling are penalized)
- **robustness** (invalid actions are handled safely and deterministically)
- **policy compliance** (terminal actions and episode boundaries are enforced)

---

## Environment overview

- **Environment class**: `MediRouteEnv` in `environment.py`
- **Spec**: `openenv.yaml`
- **Typed interface**: `models.py` (Pydantic `Observation`, `Action`, `StepResult`)
- **Tasks**: `tasks.py` (`easy`, `medium`, `hard`)
- **Deterministic graders**: `graders.py` (`grade_step`, `grade_episode`)

OpenEnv interface methods:
- `reset(difficulty: str) -> Observation`
- `step(action: Action) -> StepResult` where `StepResult` contains:
  - `observation` (updated `Observation`)
  - `reward` (incremental step reward)
  - `done` (episode termination flag)
  - `info` (diagnostics incl. totals and termination reason)
- `state() -> Observation` (read-only snapshot)

---

## Tasks (real-world healthcare cases)

The tasks represent increasing clinical risk and decision complexity.

### Easy — mild illness (primary care)
- **Scenario**: fever + sore throat with positive strep test
- **Goal**: classify **low** severity, route to **General Physician**, choose an appropriate clinic, then close with appointment/guidance
- **Clinical realism**: routine outpatient triage with lab confirmation

### Medium — suspected acute coronary syndrome
- **Scenario**: crushing chest pain, hypertension, ECG ST-elevation, elevated troponin
- **Goal**: classify **high** severity, route to **Cardiologist**, select a cardiac-capable hospital, then close appropriately
- **Clinical realism**: time-sensitive cardiology routing

### Hard — critical collapse (life-threatening)
- **Scenario**: unresponsive patient with cyanosis and SpO₂ crash
- **Goal**: classify **critical** severity and **dispatch ambulance** (terminal action), avoiding unsafe appointment flows
- **Clinical realism**: emergency escalation with irreversible harm from delay

---

## Action space

Defined in `models.py` (`VALID_ACTION_TYPES`) and mirrored in `openenv.yaml`:

- `analyze_symptoms` — classify severity (target: `low|moderate|high|critical`)
- `request_more_info` — ask for missing details (target optional)
- `recommend_specialist` — choose specialist (target: a specialist name)
- `select_hospital` — choose facility (target: a hospital name)
- `book_appointment` — close non-emergencies (target optional)
- `call_ambulance` — escalate emergencies (target optional)
- `provide_temp_guidance` — short-term guidance (target optional)

---

## Observation space

`Observation` fields (see `models.py` and `openenv.yaml`):
- `symptoms: str`
- `lab_report_summary: dict`
- `severity_score: float` in `[0.0, 1.0]` (updated when severity is analyzed)
- `location: str`
- `nearby_hospitals: list[str]`
- `available_specialists: list[str]`
- `previous_actions: list[str]` (canonical `"<action_type>:<target>"`)

---

## Reward shaping (non-binary, trajectory-based)

Reward is **shaped across the trajectory** (not a single binary outcome):
- partial credit for intermediate correct decisions (severity, specialist, hospital)
- penalties for unsafe or unproductive behavior (wrong routing, duplicates, stalling)
- episode total is clamped to `[0.0, 1.0]` for consistent scoring

Implementation:
- per-step reward: `graders.grade_step(task, action, previous_actions)`
- episode summary: `graders.grade_episode(...)`
- total reward clamped + tracked in `environment.py`

---

## Setup

### Local (Python)

```bash
cd meta
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Run the environment

### Interactive REPL (manual testing)

```bash
cd meta
python app.py --difficulty easy
```

### Baseline inference (LLM agent)

Environment variables:
- `OPENAI_API_KEY` (or `HF_TOKEN` for gated HF models)
- `API_BASE_URL` (defaults to OpenAI; can be any OpenAI-compatible server)
- `MODEL_NAME` (defaults to `gpt-4o-mini`)

```bash
cd meta
export OPENAI_API_KEY="..."
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
python inference.py --difficulty all --agent llm
```

### Baseline inference (deterministic rules agent)

This baseline runs **without any network calls** and is fully reproducible.

```bash
cd meta
python inference.py --difficulty all --agent rules
```

---

## Expected baseline scores

Because the environment and grader are deterministic:
- **Rules baseline** (`--agent rules`) is expected to score **1.0000** on `easy`, `medium`, and `hard`.
- **LLM baseline** (`--agent llm`) depends on the chosen model/endpoint, but should typically pass all tasks with a capable instruction-following model.

---

## Docker (build + run)

### Build

```bash
cd meta
docker build -t mediroute-openenv:latest .
```

### Run (rules baseline, no API required)

```bash
docker run --rm mediroute-openenv:latest python -u inference.py --difficulty all --agent rules
```

### Run (LLM baseline)

```bash
docker run --rm \
  -e OPENAI_API_KEY="..." \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  mediroute-openenv:latest python -u inference.py --difficulty all --agent llm
```

---

## Hugging Face Spaces (CPU) deployment notes

MediRoute is HF-Spaces-friendly because it is **CPU-only** and can run fully offline using the rules baseline.

Recommended Space setup:
- **SDK**: Docker (or Python, but Docker is easiest)
- **Hardware**: CPU basic
- **Entrypoint**: keep the default `CMD` (runs all tasks), or override to rules mode

If using Docker Spaces:
- add secrets as needed (`OPENAI_API_KEY` / `HF_TOKEN`)
- optionally set `MODEL_NAME` and `API_BASE_URL` for your endpoint

To default the Space to offline evaluation:
- configure it to run: `python -u inference.py --difficulty all --agent rules`

---

## Novelty (why this is different)

Compared to common OpenEnv tasks (email triage, scheduling, simple classification), MediRoute is novel because it combines:
- **safety-critical escalation** (ambulance dispatch logic, harmful appointment decisions)
- **severity inference → downstream routing** (specialist + hospital choice depends on severity)
- **trajectory shaping** that rewards incremental clinical reasoning and penalizes loops
- **healthcare-specific realism** (vitals/labs, STEMI-like signals, SpO₂ collapse)

---

## Repo map

- `environment.py` — OpenEnv environment implementation (`reset/step/state`)
- `models.py` — Pydantic models (`Observation`, `Action`, `StepResult`)
- `tasks.py` — deterministic tasks (`easy|medium|hard`)
- `graders.py` — deterministic reward shaping and episode grading
- `inference.py` — baseline inference runner (`--agent llm|rules`)
- `app.py` — manual interactive REPL
- `openenv.yaml` — OpenEnv specification

