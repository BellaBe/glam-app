#!/bin/bash
# Wait for databases to be ready

MAX_ATTEMPTS=30
ATTEMPT=1
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.local.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-glam-app}"
ENV="${ENV:-local}"

echo "Waiting for databases to be ready..."

# Function to check if a database container is ready
check_db() {
    local container=$1
    docker exec -t "$container" pg_isready -U postgres >/dev/null 2>&1
}

# Get all database containers
DB_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E ".*-db-${ENV}$" | head -5)

if [ -z "$DB_CONTAINERS" ]; then
    echo "No database containers found. Make sure infrastructure is running."
    exit 1
fi

echo "Found databases: $(echo $DB_CONTAINERS | tr '\n' ' ')"

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    ALL_READY=true

    for container in $DB_CONTAINERS; do
        if ! check_db "$container"; then
            ALL_READY=false
            break
        fi
    done

    if [ "$ALL_READY" = true ]; then
        echo "All databases are ready!"
        exit 0
    fi

    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Waiting for databases..."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

echo "Databases failed to become ready"
exit 1
