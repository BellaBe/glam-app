#!/usr/bin/env bash
set -euo pipefail

###############################################################################
#  Edit these two lines and run:  ./scripts/scaffold-service.sh
###############################################################################
SERVICE="analytics-service"          # kebab‑case slug
PY_VERSION="^3.11"
###############################################################################

# ───────────────────────── Paths ──────────────────────────────────────────── #
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(pwd)")"
BASE="${ROOT}/services/${SERVICE}"
SRC="${BASE}/src"
API_V1="${SRC}/api/v1"
CONFIG_YAML="${ROOT}/config/services/${SERVICE}.yml"

echo "📁  Creating skeleton for ${SERVICE} …"

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 1. Directory tree                                                    │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
mkdir -p \
  "${API_V1}" \
  "${SRC}"/{events/{publishers,subscribers},external,mappers,models,repositories,schemas,services} \
  "${BASE}"/{tests/{unit,integration},scripts,alembic/versions}

# Stubs for non‑Python assets
touch "${BASE}"/{Dockerfile,docker-compose.yml,README.md,Makefile,.env.example}

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 2. __init__.py everywhere                                            │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
find "${SRC}" "${BASE}/tests" -type d \( -path "*/__pycache__" -prune \) -o -type d -print \
  | while read -r dir; do touch "${dir}/__init__.py"; done

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 3. Poetry project                                                    │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
echo "🛠   Initialising Poetry project …"
(
  cd "${BASE}"
  poetry init --name "${SERVICE}" --python "${PY_VERSION}" --package-mode false --no-interaction
  poetry add fastapi uvicorn[standard] pydantic sqlalchemy asyncpg redis nats-py \
             prometheus-client httpx python-dotenv
  poetry add --editable ../../shared     # link shared package
  poetry add --group dev black isort flake8 mypy pre-commit -n
  poetry add --group test pytest pytest-asyncio pytest-cov httpx testcontainers -n
)

# ╭────────────────────────────────────────────────────────────────────────╮ #
# │ 4. Config stub                                                      │ #
# ╰────────────────────────────────────────────────────────────────────────╯ #
mkdir -p "$(dirname "${CONFIG_YAML}")"
cat > "${CONFIG_YAML}" <<EOF
service:
  name: "${SERVICE}"
api:
  external_port: 80XX
features:
  cache_enabled: true
  max_retries: 3
EOF

echo "✅  Scaffold complete:
     • service code:  services/${SERVICE}/
     • config file :  config/services/${SERVICE}.yml
     • poetry proj :  pyproject.toml inside service
Next:
  cd services/${SERVICE}
  poetry install
  make setup-dev
"
