# LifeLine AI - OpenEnv Phase 1 Validator Dockerfile
# Optimized for Backend-only compliance to bypass "HTML instead of JSON" errors
FROM python:3.11-slim

LABEL maintainer="LifeLine Team" \
      org.opencontainers.image.title="LifeLine AI - Phase 1 Backend" \
      description="Backend-only deployment for OpenEnv Phase 1 validation"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    NODE_ENV=production

# Workspace setup
WORKDIR /app

# Install system build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy the entire codebase
COPY . .

# Virtual Environment implementation (compliant with modern Linux distros)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose Hugging Face Space port
EXPOSE 7860

# --- Phase 1 Specific ---
# We ONLY start the FastAPI backend on port 7860.
# No Next.js started, no shell-redirection, no background processes.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]