# services/catalog-ai-apparel/Dockerfile
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
COPY services/catalog-ai-apparel/pyproject.toml services/catalog-ai-apparel/poetry.lock /app/

RUN poetry install --no-root --no-ansi && rm -rf ~/.cache/pypoetry ~/.cache/pip

# Copy service code
COPY services/catalog-ai-apparel /app

# -------------------
# 📦 Stage 2: Runtime
# -------------------
FROM python:3.11-slim

# Install system dependencies for ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglu1-mesa \
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

# Create models directory
RUN mkdir -p /app/models

# Start the worker
CMD ["poetry", "run", "python", "-m", "src.main"]