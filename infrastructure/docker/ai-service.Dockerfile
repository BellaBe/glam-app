# infrastructure/docker/ai-service.Dockerfile
ARG SERVICE

FROM python:3.11-slim AS builder
ARG SERVICE
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN apt-get update && apt-get install -y --no-install-recommends curl gcc g++ cmake \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /build
# Copy only metadata first
COPY services/${SERVICE}/pyproject.toml /build/pyproject.toml
COPY services/${SERVICE}/poetry.lock /build/poetry.lock

# Export and build wheels
RUN poetry export --with main -f requirements.txt > /requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /requirements.txt

# Copy code/models after deps
COPY services/${SERVICE}/ /build/service


FROM python:3.11-slim AS production
ARG SERVICE
ENV PYTHONUNBUFFERED=1 OMP_NUM_THREADS=2 OPENCV_VIDEOIO_PRIORITY_BACKEND=0

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 libgl1-mesa-glx libglu1-mesa curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

WORKDIR /app
COPY --from=builder /wheels /wheels
COPY --from=builder /requirements.txt /requirements.txt
RUN pip install --no-cache-dir --find-links=/wheels -r /requirements.txt \
    && rm -rf /wheels /requirements.txt

COPY --chown=appuser:appuser --from=builder /build/service /app

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn","src.main:app","--host","0.0.0.0","--port","8000","--workers","1"]

FROM builder AS development
WORKDIR /app
RUN poetry install --with dev --no-root && pip install watchdog
COPY --chown=appuser:appuser --from=builder /build /app
USER appuser
EXPOSE 8000
CMD ["uvicorn","src.main:app","--host","0.0.0.0","--port","8000","--reload"]
