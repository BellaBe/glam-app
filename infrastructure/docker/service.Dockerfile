# infrastructure/docker/service.Dockerfile
ARG SERVICE

FROM python:3.11-slim AS builder
ARG SERVICE
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Build deps only here
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc g++ build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry in builder
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /build

# Copy only lock metadata first for cache
# Shared layer
COPY shared/pyproject.toml /build/shared/pyproject.toml
COPY shared/poetry.lock /build/shared/poetry.lock
# Service layer
COPY services/${SERVICE}/pyproject.toml /build/service/pyproject.toml
COPY services/${SERVICE}/poetry.lock /build/service/poetry.lock

# Export fully pinned requirements from locks
# Remove editable lines if any
RUN cd /build/shared  && poetry export --with main -f requirements.txt | sed '/^-e /d' > /req-shared.txt
RUN cd /build/service && poetry export --with main -f requirements.txt | sed '/^-e /d' > /req-svc.txt
RUN cat /req-shared.txt /req-svc.txt > /requirements.txt

# Build wheels for offline deterministic installs
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /requirements.txt

# Now copy source (after deps for better caching)
COPY shared /build/shared
COPY services/${SERVICE} /build/service

# Optional: build local wheels for your own packages if they are proper PEP 517 packages
# RUN pip install build && python -m build /build/shared -o /dist && python -m build /build/service -o /dist && \
#     pip wheel --no-cache-dir --wheel-dir /wheels /dist/*.whl

FROM python:3.11-slim AS production
ARG SERVICE
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

WORKDIR /app

# Install from wheels exactly
COPY --from=builder /wheels /wheels
COPY --from=builder /requirements.txt /requirements.txt
RUN pip install --no-cache-dir --find-links=/wheels -r /requirements.txt \
    && rm -rf /wheels /requirements.txt

# Bring application code
COPY --chown=appuser:appuser --from=builder /build/shared /shared
COPY --chown=appuser:appuser --from=builder /build/service /app
RUN chown -R appuser:appuser /app /shared

USER appuser
EXPOSE 8000

# Migrations via module invocation to avoid missing console scripts
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "sleep $((RANDOM % 10)) && if [ -d alembic ]; then python -m alembic upgrade head; fi && exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1"]

# Dev target keeps Poetry if you need it
FROM builder AS development
ARG SERVICE
RUN cd /build/shared  && poetry install --with dev --no-root && \
    cd /build/service && poetry install --with dev --no-root && \
    pip install watchdog
WORKDIR /app
COPY --chown=appuser:appuser --from=builder /build/shared /shared
COPY --chown=appuser:appuser --from=builder /build/service /app
USER appuser
EXPOSE 8000
CMD ["uvicorn","src.main:app","--host","0.0.0.0","--port","8000","--reload"]
