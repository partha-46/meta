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
        ca-certificates \
        gnupg \
        build-essential \
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
COPY backend/requirements.txt ./backend-requirements.txt
RUN if [ -f ./backend-requirements.txt ]; then \
            pip install --no-cache-dir -r ./backend-requirements.txt; \
        fi

# Backwards-compat: install lifeline-ai/backend/requirements.txt if present
COPY lifeline-ai/backend/requirements.txt ./lifeline-ai-backend-requirements.txt
RUN if [ -f ./lifeline-ai-backend-requirements.txt ]; then \
                    pip install --no-cache-dir -r ./lifeline-ai-backend-requirements.txt; \
                fi

# ── Copy application source safely ────────────────────────────────────────────
# Copying the full project avoids file-not-found build breaks and is HF-Spaces-friendly.
COPY . .

# Install Node.js and build the Next.js frontend (do this as root before switching user)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm ci --prefix lifeline-ai --no-audit --no-fund || npm install --prefix lifeline-ai \
    && npm run build --prefix lifeline-ai

# ── Non-root user for security ────────────────────────────────────────────────
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# ── Environment variable defaults (override at runtime) ───────────────────────
ENV OPENAI_API_KEY="EMPTY" \
    API_BASE_URL="https://api.openai.com/v1" \
    MODEL_NAME="gpt-4o-mini" \
    HF_TOKEN=""

# ── Expose the port expected by Hugging Face Spaces (frontend)
EXPOSE 7860

# Default command: start backend on 8000 (background) and run Next.js frontend on 7860
# The frontend proxies /api to the backend via next.config.js rewrites.
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 & exec npm run start --prefix lifeline-ai -- -p 7860"]
