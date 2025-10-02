# services/selfie-ai-analyzer/Dockerfile

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-dev \
    # Additional build tools
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy dependency files first (for better caching)
COPY pyproject.toml poetry.lock* ./

# Copy shared package (assuming it's at the same level)
COPY ../shared /shared

# Install dependencies
RUN poetry install --no-root --only main --no-interaction --no-ansi

# Copy application code
COPY ./src ./src

# Install the package itself
RUN poetry install --only-root

# Download ML models during build (to avoid runtime download)
RUN python -c "import mediapipe; import deepface" || true

# Pre-download DeepFace models
RUN python -c "\
from deepface import DeepFace; \
import cv2; \
import numpy as np; \
# Create a dummy image to trigger model download \
dummy_img = np.zeros((224, 224, 3), dtype=np.uint8); \
cv2.imwrite('/tmp/dummy.jpg', dummy_img); \
try: \
    DeepFace.analyze('/tmp/dummy.jpg', \
                     actions=['age', 'gender', 'race'], \
                     enforce_detection=False, \
                     detector_backend='opencv'); \
except: \
    pass" || true

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim AS runtime

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV runtime dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1 \
    libglu1-mesa \
    # Video/image processing
    ffmpeg \
    libavcodec-extra \
    # System utilities
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src /app/src

# Copy shared package
COPY --from=builder /shared /shared

# Copy pre-downloaded models from builder
COPY --from=builder /root/.deepface /home/appuser/.deepface
COPY --from=builder /root/.keras /home/appuser/.keras

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:/shared:$PYTHONPATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # DeepFace settings
    DEEPFACE_HOME="/home/appuser/.deepface" \
    # TensorFlow settings (reduce memory usage)
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_ENABLE_ONEDNN_OPTS=0 \
    # OpenCV settings
    OPENCV_VIDEOIO_PRIORITY_MSMF=0 \
    # Service settings
    APP_ENV=production \
    SELFIE_ANALYZER_API_EXTERNAL_PORT=8127

# Create temp directory for analysis
RUN mkdir -p /tmp/selfies && chown -R appuser:appuser /tmp/selfies

# Create models directory and set permissions
RUN mkdir -p /models && chown -R appuser:appuser /models

# Change ownership of the app directory
RUN chown -R appuser:appuser /app /home/appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8027/health || exit 1

# Switch to non-root user
USER appuser

# Expose port (internal service port)
EXPOSE 8027

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8027", "--workers", "1"]