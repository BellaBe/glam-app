FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry==1.6.1
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Copy shared package (relative to service directory)
COPY ../../shared /shared

# Install dependencies
RUN poetry install --no-dev --no-root

# Copy application
COPY . .

# Install application
RUN poetry install --no-dev

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy from build stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /app /app

# Copy config directory structure (non-secret configs)
COPY config /app/config

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8016/health').raise_for_status()"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8016"]