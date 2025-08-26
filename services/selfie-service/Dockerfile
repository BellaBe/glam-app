FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and Pillow
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy shared package
COPY ../shared /shared

# Copy application code
COPY . .

# Generate Prisma client
RUN prisma generate

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
