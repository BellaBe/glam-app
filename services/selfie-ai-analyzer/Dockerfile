# services/selfie-ai-analyzer/Dockerfile
# ──────────────────────────────────────────────────────────────
# 📦  Stage 1 ─ Builder
# ──────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ARG SERVICE=selfie-ai-analyzer
ARG POETRY_VERSION=1.8.3

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Build dependencies for OpenCV/MediaPipe
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc g++ python3-dev curl ca-certificates \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 libgl1 \
 && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==${POETRY_VERSION} nodejs-bin
RUN poetry config virtualenvs.create false

# Install shared dependencies
COPY shared /shared
WORKDIR /shared
RUN poetry install --only main --no-ansi

# Install service dependencies
WORKDIR /app
COPY services/${SERVICE}/pyproject.toml services/${SERVICE}/poetry.lock* ./
RUN poetry install --only main --no-ansi

# Generate Prisma client if schema exists
COPY services/${SERVICE}/prisma* ./prisma/
RUN if [ -f "prisma/schema.prisma" ]; then prisma generate; fi

# Copy service source
COPY services/${SERVICE} /app

# Create empty model directories so COPY won't fail in next stage
RUN mkdir -p /root/.deepface /root/.keras

# ──────────────────────────────────────────────────────────────
# 🚀  Stage 2 ─ Runtime
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONPATH="/shared:/app" \
    DOCKER_CONTAINER=1 \
    PYTHONUNBUFFERED=1 \
    DEEPFACE_HOME="/app/.deepface" \
    TF_CPP_MIN_LOG_LEVEL=2 \
    OMP_NUM_THREADS=2 \
    OPENBLAS_NUM_THREADS=2

WORKDIR /app

# Runtime libraries for OpenCV
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgl1 curl \
 && rm -rf /var/lib/apt/lists/*

# Copy Python environment and app
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
COPY --from=builder /shared /shared

# Create model directories in runtime (models will download on first use)
RUN mkdir -p /app/.deepface /app/.keras

# Non-root user
RUN useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
