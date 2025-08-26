#!/bin/bash
# Database restore script for GLAM You Up

set -euo pipefail

BACKUP_DATE=${1:-}
BACKUP_DIR="/var/backups/glam"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 YYYYMMDD_HHMMSS"
    echo "Available backups:"
    ls -la $BACKUP_DIR/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$BACKUP_DIR/backup_${BACKUP_DATE}.tar.gz"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from $BACKUP_FILE..."
read -p "This will overwrite current databases. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 1
fi

# Extract backup
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Restore each database
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
    "selfie_db"
    "token_db"
    "webhook_db"
)

for db in "${DATABASES[@]}"; do
    if [ -f "$TEMP_DIR/${db}.dump" ]; then
        echo "Restoring $db..."
        docker exec -i glam-postgres pg_restore -U postgres -d "$db" -c < "$TEMP_DIR/${db}.dump" || echo "Failed to restore $db"
    fi
done

rm -rf "$TEMP_DIR"
echo "Restore complete!"