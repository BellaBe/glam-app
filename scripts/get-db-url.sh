#!/bin/bash
# Generate DATABASE_URL for a service

SERVICE=$1
ENV=${2:-local}

# Convert service name to env variable prefix
SERVICE_PREFIX=$(echo $SERVICE | sed 's/-service//' | sed 's/-/_/g' | tr '[:lower:]' '[:upper:]')

# Source environment files
[ -f .env ] && source .env
[ -f .env.$ENV ] && source .env.$ENV

# Get database configuration
DB_USER_VAR="${SERVICE_PREFIX}_DB_USER"
DB_PASS_VAR="${SERVICE_PREFIX}_DB_PASSWORD"
DB_NAME_VAR="${SERVICE_PREFIX}_DB_NAME"
DB_PORT_VAR="${SERVICE_PREFIX}_DB_PORT_EXTERNAL"

DB_USER=${!DB_USER_VAR:-$DB_USER}
DB_PASS=${!DB_PASS_VAR:-$DB_PASSWORD}
DB_NAME=${!DB_NAME_VAR:-${SERVICE/-/_}_db}
DB_PORT=${!DB_PORT_VAR:-5432}

# Determine host based on environment
case $ENV in
    local)
        DB_HOST="localhost"
        ;;
    dev|prod)
        DB_HOST="postgres"
        ;;
    *)
        DB_HOST="localhost"
        ;;
esac

echo "postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
