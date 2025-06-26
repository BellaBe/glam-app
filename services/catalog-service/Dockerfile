# services/catalog-service/Dockerfile
# -------------------
# 🛠 Stage 1: Builder
# -------------------
FROM python:3.11-slim AS builder

RUN pip install --no-cache-dir poetry==1.7.1

ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1

WORKDIR /app

ARG CACHE_BUSTER=1

# Install shared package
COPY shared /shared
RUN pip install --no-cache-dir -e /shared

ENV PYTHONPATH="/shared:/app:${PYTHONPATH}"

# Install service dependencies
COPY services/catalog-service/pyproject.toml services/catalog-service/poetry.lock /app/

RUN poetry install --no-root --no-ansi && rm -rf ~/.cache/pypoetry ~/.cache/pip

# Copy service code
COPY services/catalog-service /app

# -------------------
# 📦 Stage 2: Runtime
# -------------------
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.7.1

ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1

WORKDIR /app

ENV PYTHONPATH="/shared:/app:${PYTHONPATH}"

# Copy from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
COPY --from=builder /shared /shared

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn server
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]