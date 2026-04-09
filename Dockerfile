# LifeLine AI - Spaces-ready Dockerfile
FROM node:20-slim

LABEL maintainer="LifeLine Team" \
      org.opencontainers.image.title="LifeLine AI" \
      description="Next.js frontend with optional Python FastAPI backend (Hugging Face Spaces ready)"

ENV NODE_ENV=production \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Root workspace
WORKDIR /app

# Install system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         python3 python3-pip ca-certificates curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy entire repo first
COPY . .

# Move into frontend folder
WORKDIR /app/lifeline-ai

# Install frontend dependencies
RUN if [ -f package-lock.json ]; then \
      npm ci --no-audit --no-fund; \
    else \
      npm install --no-audit --no-fund; \
    fi

# Build frontend
RUN npm run build

# Install backend dependencies if available
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose HF Space port
EXPOSE 7860

# Run backend + frontend
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 2>/dev/null & cd /app/lifeline-ai && exec npm run start -- -p 7860"]