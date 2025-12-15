# Worker Service Dockerfile (CPU - with OCR dependencies)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    C_FORCE_ROOT=true

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    libmagic1 \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY backend/requirements-base.txt .
COPY backend/requirements-ocr.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-base.txt && \
    pip install --no-cache-dir -r requirements-ocr.txt

# Copy application code
COPY backend/ .

# Health check for worker
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD celery -A config inspect ping -d celery@$HOSTNAME || exit 1

# Default command (overridden by docker-compose)
CMD ["celery", "-A", "config", "worker", "--loglevel=info"]
