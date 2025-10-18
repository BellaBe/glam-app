#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/glam}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${DATE}"
RETENTION_DAYS=7
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

mkdir -p "${BACKUP_PATH}"

echo "Starting backup at $(date)"

DATABASES=(
    "analytics_db"
    "billing_db"
    "catalog_db"
    "credit_db"
    "merchant_db"
    "notification_db"
    "recommendation_db"
    "season_compatibility_db"
    "selfie_db"
    "token_db"
    "webhook_db"
)

for db in "${DATABASES[@]}"; do
    echo "  Backing up ${db}..."
    docker compose exec -T postgres pg_dump -U postgres -Fc "${db}" > "${BACKUP_PATH}/${db}.dump"
done

# Backup config (without secrets)
echo "Backing up configuration..."
grep -v "PASS\|KEY\|SECRET\|TOKEN" .env.prod > "${BACKUP_PATH}/env.backup" 2>/dev/null || true

# Compress
echo "Compressing backup..."
tar -czf "${BACKUP_PATH}.tar.gz" -C "${BACKUP_DIR}" "${DATE}"
rm -rf "${BACKUP_PATH}"

# Cleanup old backups
echo "Cleaning old backups..."
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "✅ Backup completed: ${BACKUP_PATH}.tar.gz"
echo "   Size: $(du -h ${BACKUP_PATH}.tar.gz | cut -f1)"
