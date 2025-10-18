# ──────────────────────────────────────────────────────────────
# 📦  Stage 1 ─ Builder
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ARG SERVICE=catalog-ai-analyzer
ARG CACHE_BUSTER=1
ARG POETRY_VERSION=1.8.3

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_INSTALLER_PARALLEL=false \
    POETRY_HTTP_TIMEOUT=600 \
    POETRY_MAX_RETRIES=5 \
    PIP_DEFAULT_TIMEOUT=120 \
    PRISMA_USE_NODEJS_BIN=true \
    PRISMA_USE_GLOBAL_NODE=false \
    DEEPFACE_HOME=/root/.deepface

WORKDIR /app

# Build deps incl. OpenCV needs
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc g++ python3-dev \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    wget curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
 && poetry config virtualenvs.create false

# Preinstall uvicorn[standard] deps as wheels to avoid flaky downloads
RUN python -m pip install --no-cache-dir --only-binary=:all: \
    "uvloop==0.21.0" "httptools==0.6.4" "websockets==15.0.1" \
    "watchfiles==1.1.0" "python-dotenv==1.1.1"

# Provide Node to Prisma via nodejs-bin (prevents nodeenv path)
RUN pip install --no-cache-dir nodejs-bin

RUN echo "Cache bust value: ${CACHE_BUSTER}"

# 1) Shared deps
COPY shared /shared
WORKDIR /shared
RUN test -f poetry.lock || (echo "shared/poetry.lock missing" && exit 1)
RUN poetry install --only main --no-interaction --no-ansi

# 2) Service deps
WORKDIR /app
COPY services/${SERVICE}/pyproject.toml services/${SERVICE}/poetry.lock* ./
RUN test -f poetry.lock || (echo "services/${SERVICE}/poetry.lock missing" && exit 1)
RUN poetry install --only main --no-interaction --no-ansi

# 3) Prisma client if schema exists
COPY services/${SERVICE}/prisma* ./prisma/
RUN if [ -f "prisma/schema.prisma" ]; then prisma generate; fi

# 4) Pre-download ML models (cached into /root/.deepface and /root/.keras)
RUN python - <<'PY' || true
import mediapipe, os
from deepface import DeepFace
import cv2, numpy as np
os.makedirs("/tmp", exist_ok=True)
img = np.zeros((224,224,3), dtype=np.uint8)
cv2.imwrite("/tmp/dummy.jpg", img)
try:
    DeepFace.analyze("/tmp/dummy.jpg",
                     actions=['age','gender','race'],
                     enforce_detection=False,
                     detector_backend='opencv')
except Exception:
    pass
PY

# 5) Service source
COPY services/${SERVICE} /app

# ──────────────────────────────────────────────────────────────
# 🚀  Stage 2 ─ Runtime
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

ARG SERVICE=catalog-ai-analyzer

ENV PYTHONPATH="/shared:/app" \
    DOCKER_CONTAINER=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    DEEPFACE_HOME="/home/appuser/.deepface" \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_ENABLE_ONEDNN_OPTS=0 \
    OPENCV_VIDEOIO_PRIORITY_MSMF=0 \
    # limit BLAS thread explosions
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

WORKDIR /app

# Runtime libs only
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgl1 curl \
 && rm -rf /var/lib/apt/lists/*

# Copy from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
COPY --from=builder /shared /shared

# Model caches → runtime home
COPY --from=builder /root/.deepface /home/appuser/.deepface
COPY --from=builder /root/.keras /home/appuser/.keras

# Non-root
RUN useradd -m -u 1000 appuser \
 && mkdir -p /tmp/selfies /models \
 && chown -R appuser:appuser /app /tmp/selfies /models /home/appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
