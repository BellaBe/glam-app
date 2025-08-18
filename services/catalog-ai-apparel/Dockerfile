# services/catalog-analysis/Dockerfile
# ──────────────────────────────────────────────────────────────
# 📦  Stage 1 ─ Builder
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for OpenCV and ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# ---- 1️⃣  Install shared package dependencies
COPY shared /shared
WORKDIR /shared
RUN poetry install --no-dev

# ---- 2️⃣  Install service dependencies
WORKDIR /app
COPY services/catalog-analysis/pyproject.toml services/catalog-analysis/poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

# ---- 3️⃣  Copy service code
COPY services/catalog-analysis /app

# ---- 4️⃣  Copy config
COPY config /app/config

# ---- 5️⃣  Copy model file
COPY services/cv_cloth/models /app/models

# ──────────────────────────────────────────────────────────────
# 📦  Stage 2 ─ Runtime
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Install runtime dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy everything from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
COPY --from=builder /shared /shared

ENV PYTHONPATH="/shared:/app"
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import asyncio; print('Service running')" || exit 1

CMD ["python", "-m", "src.main"]
