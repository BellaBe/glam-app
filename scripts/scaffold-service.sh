#!/usr/bin/env bash
set -euo pipefail

###############################################################################
#  GLAM Service Scaffold Script - Creates skeleton only
#  Edit these variables and run:  ./scripts/scaffold-service.sh
###############################################################################
SERVICE_NAME="season-compatibility-service"          # kebab-case slug
PY_VERSION="^3.11"
###############################################################################

# ───────────────────────── Paths ──────────────────────────────────────────── #
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(pwd)")"
BASE="${ROOT}/services/${SERVICE_NAME}"
SRC="${BASE}/src"
API_V1="${SRC}/api/v1"

echo "📁  Creating GLAM service skeleton for ${SERVICE_NAME} …"

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 1. Directory structure (following GLAM standard)                        │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
mkdir -p \
  "${API_V1}" \
  "${SRC}/events" \
  "${SRC}/external" \
  "${SRC}/repositories" \
  "${SRC}/schemas" \
  "${SRC}/services" \
  "${BASE}/prisma" \
  "${BASE}/tests/unit" \
  "${BASE}/tests/integration"

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 2. Create empty Python files                                            │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #

# Create __init__.py files
find "${SRC}" "${BASE}/tests" -type d \( -path "*/__pycache__" -prune \) -o -type d -print \
  | while read -r dir; do touch "${dir}/__init__.py"; done

# Core files
touch "${SRC}/main.py"
touch "${SRC}/config.py"
touch "${SRC}/lifecycle.py"
touch "${SRC}/dependencies.py"
touch "${SRC}/exceptions.py"

# API files
touch "${API_V1}/endpoints.py"

# Event files
touch "${SRC}/events/publishers.py"
touch "${SRC}/events/listeners.py"

# Repository files (example)
touch "${SRC}/repositories/base_repository.py"

# Service files (example)
touch "${SRC}/services/domain_service.py"

# Schema files (example)
touch "${SRC}/schemas/domain.py"
touch "${SRC}/schemas/events.py"

# External integrations (if needed)
touch "${SRC}/external/__init__.py"

# Test files
touch "${BASE}/tests/unit/test_service.py"
touch "${BASE}/tests/integration/test_api.py"
touch "${BASE}/tests/conftest.py"


# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 3. Create Prisma schema template                                        │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
cat > "${BASE}/prisma/schema.prisma" <<EOF
generator client {
  provider             = "prisma-client-py"
  interface            = "asyncio"
  recursive_type_depth = 5
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// Add your models here
EOF

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 4. Create Dockerfile                                                    │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
cat > "${BASE}/Dockerfile" <<EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./
COPY ../shared /shared

# Install dependencies
RUN poetry config virtualenvs.create false \\
    && poetry install --no-interaction --no-ansi

# Copy application code
COPY . .

# Generate Prisma client
RUN poetry run prisma generate

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 5. Poetry project with GLAM dependencies                                │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
echo "🛠   Initializing Poetry project …"
(
  cd "${BASE}"

  # Configure Poetry to create .venv inside the project
  poetry config virtualenvs.in-project true --local

  # Initialize project
  poetry init \
    --name "${SERVICE_NAME}" \
    --description "${SERVICE_NAME} microservice for GLAM platform" \
    --author "GLAM Team" \
    --python "${PY_VERSION}" \
    --no-interaction

  echo "📦  Installing dependencies (this may take a moment)..."

  # Core dependencies
  poetry add \
    fastapi@^0.109 \
    "uvicorn[standard]" \
    pydantic \
    prisma \
    numpy \
    scipy \
    --no-interaction

  # Add shared package from monorepo
  poetry add --editable ../../shared --no-interaction

  # Dev dependencies
  poetry add --group dev \
    pytest \
    ruff \
    --no-interaction
)

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 6. Update root .env template if it exists                              │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
if [ -f "${ROOT}/.env.example" ]; then
  echo "" >> "${ROOT}/.env.example"
  echo "# ${SERVICE_NAME} configuration" >> "${ROOT}/.env.example"
  echo "${SERVICE_NAME^^}_API_EXTERNAL_PORT=80XX" >> "${ROOT}/.env.example"
  echo "${SERVICE_NAME^^}_DB_ENABLED=true" >> "${ROOT}/.env.example"
fi

echo "
✅  Scaffold complete for ${SERVICE_NAME}

📁 Structure created:
   services/${SERVICE_NAME}/
   ├── .venv/                   # Local virtual environment (after poetry install)
   ├── .vscode/                 # VS Code settings
   ├── src/
   │   ├── main.py              # FastAPI app entry
   │   ├── config.py            # Service configuration
   │   ├── lifecycle.py         # Service lifecycle management
   │   ├── dependencies.py      # Dependency injection
   │   ├── exceptions.py        # Domain exceptions
   │   ├── api/v1/
   │   │   └── endpoints.py     # API endpoints
   │   ├── schemas/
   │   │   ├── domain.py        # Pydantic DTOs
   │   │   └── events.py        # Event schemas
   │   ├── repositories/        # Data access layer
   │   ├── services/            # Business logic
   │   └── events/
   │       ├── publishers.py    # Event publishers
   │       └── listeners.py     # Event listeners
   ├── prisma/
   │   └── schema.prisma        # Database schema
   ├── tests/
   │   ├── unit/
   │   └── integration/
   ├── Dockerfile
   └── pyproject.toml

📝 Next steps:
   1. cd services/${SERVICE_NAME}
   2. poetry install           # Creates .venv in the service directory
   3. poetry shell             # Activate the virtual environment
   4. Add DATABASE_URL to root .env
   5. Define your Prisma models in prisma/schema.prisma
   6. poetry run prisma generate
   7. poetry run prisma migrate dev --name init
   8. Implement following the GLAM implementation guide

💡 Tips:
   - Virtual environment is at: services/${SERVICE_NAME}/.venv
   - Use 'poetry shell' or 'source .venv/bin/activate' to activate
   - VS Code will auto-detect the .venv if you open the service folder

🔗 Implementation guide: docs/implementation-guide.md
"
