#!/bin/bash
# scripts/backup.sh
# Daily backup script for GLAM platform

set -e

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${DATE}"
RETENTION_DAYS=7

# Create backup directory
mkdir -p "${BACKUP_PATH}"

echo "Starting backup at $(date)"

# Backup all PostgreSQL databases
echo "Backing up databases..."
DATABASES=(
    "shopify_session_db"
    "analytics_db"
    "billing_db"
    "catalog_db"
    "credit_db"
    "merchant_db"
    "notification_db"
    "recommendation_db"
    "season_compatibility_db"
    "selfie_db",
    "token_db"
    "webhook_db"
)

for db in "${DATABASES[@]}"; do
    echo "  Backing up ${db}..."
    docker exec glam_postgres pg_dump -U postgres -Fc "${db}" > "${BACKUP_PATH}/${db}.dump"
done

# Backup environment file (without secrets)
echo "Backing up configuration..."
grep -v "PASS\|KEY\|SECRET" .env > "${BACKUP_PATH}/env.backup" || true

# Create compressed archive
echo "Compressing backup..."
tar -czf "${BACKUP_PATH}.tar.gz" -C "${BACKUP_DIR}" "${DATE}"
rm -rf "${BACKUP_PATH}"

# Remove old backups
echo "Cleaning old backups..."
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup completed: ${BACKUP_PATH}.tar.gz"
echo "Backup size: $(du -h ${BACKUP_PATH}.tar.gz | cut -f1)"