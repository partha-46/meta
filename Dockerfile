# ── Base image (lightweight, CPU-only) ────────────────────────────────────────
FROM python:3.11-slim

# ── Metadata ──────────────────────────────────────────────────────────────────
LABEL maintainer="MediRoute Team" \
      env_id="mediroute-openenv-v1" \
      version="1.0.0" \
      description="Medical Triage and Hospital Routing OpenEnv Environment" \
      org.opencontainers.image.title="MediRoute OpenEnv" \
      org.opencontainers.image.licenses="MIT"

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python runtime defaults ───────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies first (cache-friendly layer) ──────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# If a backend requirements file exists (lifeline-ai/backend/requirements.txt), install it too
COPY lifeline-ai/backend/requirements.txt ./lifeline-backend-requirements.txt
RUN if [ -f ./lifeline-backend-requirements.txt ]; then \
      pip install --no-cache-dir -r ./lifeline-backend-requirements.txt; \
    fi

# ── Copy application source safely ────────────────────────────────────────────
# Copying the full project avoids file-not-found build breaks and is HF-Spaces-friendly.
COPY . .

# ── Non-root user for security ────────────────────────────────────────────────
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# ── Environment variable defaults (override at runtime) ───────────────────────
ENV OPENAI_API_KEY="EMPTY" \
    API_BASE_URL="https://api.openai.com/v1" \
    MODEL_NAME="gpt-4o-mini" \
    HF_TOKEN=""

# ── Expose the port expected by Hugging Face Spaces and run the backend web server
EXPOSE 7860

# Default command: start the FastAPI backend (lifeline-ai backend) on port 7860.
# This keeps the container running as a web service compatible with Spaces (sdk: docker).
# It will cd into the backend folder and run uvicorn. Override at runtime as needed.
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port 7860"]
