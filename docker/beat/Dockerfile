# Beat Service Dockerfile (Optimized - No OCR dependencies)
# Celery Beat scheduler - only needs base dependencies
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    C_FORCE_ROOT=true

# Set work directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only base requirements (no OCR dependencies)
COPY backend/requirements-base.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-base.txt

# Copy application code
COPY backend/ .

# Default command (overridden by docker-compose)
CMD ["celery", "-A", "config", "beat", "--loglevel=info"]
