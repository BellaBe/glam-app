# ──────────────────────────────────────────────────────────────
# 📦  Stage 1 ─ Builder
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim as builder

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.6.1
RUN pip install poetry==$POETRY_VERSION

# Copy shared package first
WORKDIR /shared
COPY shared/pyproject.toml shared/poetry.lock* ./
COPY shared/ ./

# Install shared dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy service source
COPY services/webhook-service /app

# ──────────────────────────────────────────────────────────────
# 📦  Stage 2 ─ Runtime
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Copy everything from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app       /app
COPY --from=builder /shared    /shared

ENV PYTHONPATH="/shared:/app"
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8012

# Run with optimal settings
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8012", "--workers", "4"]