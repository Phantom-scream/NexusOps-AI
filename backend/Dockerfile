# ============================================================
# NexusOps AI — Backend Dockerfile
# Multi-stage build for development and production
# ============================================================

FROM python:3.12-slim AS base

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management, plus setuptools (provides pkg_resources)
RUN pip install uv setuptools

WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# ============================================================
# Development Stage
# ============================================================
FROM base AS development

RUN uv pip install --system -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]

# ============================================================
# Production Stage
# ============================================================
FROM base AS production

RUN uv pip install --system -r requirements.txt --no-cache

COPY . .

# Non-root user for security
RUN useradd -m -u 1000 nexusops && chown -R nexusops:nexusops /app
USER nexusops

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
