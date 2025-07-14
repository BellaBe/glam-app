# ──────────────────────────────────────────────────────────────
# 🛠  Stage 1  ─ Builder
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Base toolchain
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# ---- 1️⃣  Copy shared lib -----------------------------------------------------
COPY shared /shared
RUN pip install --no-cache-dir -e /shared

# Make shared importable
ENV PYTHONPATH="/shared:/app"

# ---- 2️⃣  Service deps --------------------------------------------------------
COPY services/notification-service/pyproject.toml \
     services/notification-service/poetry.lock* /app/
RUN poetry install --no-root --no-ansi \
    && rm -rf ~/.cache/pypoetry ~/.cache/pip

# ---- 3️⃣  Copy service source -------------------------------------------------
COPY services/notification-service /app

# ---- 4️⃣  Copy config -----------------------------------------------------

COPY config /app/config

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

EXPOSE 8000

# Run with optimal settings for notification service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]