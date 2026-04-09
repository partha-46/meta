# LifeLine AI - Spaces-ready Dockerfile
FROM node:20-slim

LABEL maintainer="LifeLine Team" \
      org.opencontainers.image.title="LifeLine AI" \
      description="Next.js frontend with optional Python FastAPI backend (Hugging Face Spaces ready)"

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Root workspace
WORKDIR /app

# Install system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         python3 python3-pip python3-venv ca-certificates curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy entire repo first
COPY . .

# Move into frontend folder
WORKDIR /app/lifeline-ai

# Install ALL dependencies (including devDependencies needed for build)
# NODE_ENV is NOT set to production here — that would skip devDeps and break the build
RUN npm ci --include=dev --no-audit --no-fund

# Build frontend
RUN npm run build

# Install backend dependencies if available (using virtual environment)
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose HF Space port
EXPOSE 7860

# Set production mode at runtime only (not at build time)
ENV NODE_ENV=production

# Run backend as the primary app for OpenEnv validation
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]