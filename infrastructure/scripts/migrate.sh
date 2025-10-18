# Create infrastructure/scripts/migrate.sh
#!/bin/bash
set -euo pipefail

DB_URL=$1
LOCKFILE="/tmp/migration.lock"

exec 200>$LOCKFILE
flock -w 300 200 || exit 1

if [ -d alembic ]; then
    python -m alembic upgrade head
fi