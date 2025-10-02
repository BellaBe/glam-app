# services/recommendation-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared package first
COPY shared/ /shared/
WORKDIR /shared
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy service code
WORKDIR /app
COPY services/recommendation-service/pyproject.toml services/recommendation-service/poetry.lock ./
RUN poetry install --no-dev

# Copy application code
COPY services/recommendation-service/src ./src
COPY services/recommendation-service/prisma ./prisma

# Generate Prisma client
RUN prisma generate

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8025

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8025"]