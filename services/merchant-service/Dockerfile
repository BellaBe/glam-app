# ──────────────────────────────────────────────────────────────
# 📦  Stage 1 ─ Builder
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Allow re-use for any service; default keeps backward compatibility
ARG SERVICE=merchant-service

# Bump this to force layer invalidation (or pass via compose)
ARG CACHE_BUSTER=1

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Minimal build deps (gcc often required for some wheels)
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc \
 && rm -rf /var/lib/apt/lists/*

# Install Poetry (system-wide, no venvs)
ARG POETRY_VERSION=1.8.3
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
 && poetry config virtualenvs.create false

# ---- 0️⃣  Cache bust marker (forces rebuild when you change the arg)
RUN echo "Cache bust value: ${CACHE_BUSTER}"

# ---- 1️⃣  Install shared package deps
COPY shared /shared
WORKDIR /shared
RUN poetry install --no-dev --no-interaction --no-ansi

# ---- 2️⃣  Install service deps (copy only manifests first for better caching)
WORKDIR /app
# Copy service manifests (pyproject & optional lock)
COPY services/${SERVICE}/pyproject.toml services/${SERVICE}/poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

# ---- 3️⃣  Copy Prisma schema and generate client
# (prisma is provided by prisma-client-py; generation happens here)
COPY services/${SERVICE}/prisma ./prisma
RUN prisma generate

# ---- 4️⃣  Copy service source
# (copy last to maximize cache hits on deps & generated client)
COPY services/${SERVICE} /app

# ──────────────────────────────────────────────────────────────
# 🚀  Stage 2 ─ Runtime
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

ARG SERVICE=merchant-service

ENV PYTHONPATH="/shared:/app" \
    DOCKER_CONTAINER=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed libs, built app, and shared code from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
COPY --from=builder /shared /shared

# Non-root user
RUN useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run migrations then start API
# (prisma CLI is available because poetry installed into system site-packages)
CMD ["sh", "-c", "prisma migrate deploy && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
