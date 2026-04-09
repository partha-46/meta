# LifeLine AI - Spaces-ready Dockerfile (clean, repo-root centric)
FROM node:20-slim

LABEL maintainer="LifeLine Team" \
      org.opencontainers.image.title="LifeLine AI" \
      description="Next.js frontend with optional Python FastAPI backend (Hugging Face Spaces ready)"

ENV NODE_ENV=production \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install minimal system deps (python + build tools)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         python3 python3-pip ca-certificates curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Node package manifests and install Node deps from repo root
COPY package*.json ./
RUN if [ -f package-lock.json ]; then \
      npm ci --no-audit --no-fund; \
    else \
      npm install --no-audit --no-fund; \
    fi

# Install Python dependencies from repo-root requirements.txt only
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the repository and build the Next.js frontend
COPY . .
RUN npm run build

# Expose the UI port for Hugging Face Spaces
EXPOSE 7860

# Start backend (if present) on localhost:8000 in background, then run Next.js frontend on 7860
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 2>/dev/null & exec npm run start -- -p 7860"]
