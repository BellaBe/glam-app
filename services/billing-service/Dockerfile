# services/billing-service/Dockerfile
# Stage 1 - Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Install shared package dependencies
COPY shared /shared
WORKDIR /shared
RUN poetry install --no-dev

# Install service dependencies
WORKDIR /app
COPY services/billing-service/pyproject.toml services/billing-service/poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy Prisma schema and generate client
COPY services/billing-service/prisma ./prisma
RUN prisma generate

# Copy service code
COPY services/billing-service /app

# Copy config
COPY config /app/config

# Stage 2 - Runtime
FROM python:3.11-slim

# Copy everything from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
COPY --from=builder /shared /shared

ENV PYTHONPATH="/shared:/app"
ENV DOCKER_CONTAINER=1

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "prisma migrate deploy && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
