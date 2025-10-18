#!/bin/bash
set -euo pipefail

BACKUP_DATE=${1:-}
BACKUP_DIR="${BACKUP_DIR:-/var/backups/glam}"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 YYYYMMDD_HHMMSS"
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$BACKUP_DIR/${BACKUP_DATE}.tar.gz"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from $BACKUP_FILE..."
read -p "This will OVERWRITE current databases. Continue? (yes/NO) " -r
if [[ ! $REPLY == "yes" ]]; then
    echo "Aborted"
    exit 1
fi

TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

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
    dump_file="$TEMP_DIR/${BACKUP_DATE}/${db}.dump"
    if [ -f "$dump_file" ]; then
        echo "Restoring $db..."
        docker compose exec -T postgres pg_restore -U postgres -d "$db" --clean --if-exists < "$dump_file" || echo "⚠️  Failed to restore $db"
    else
        echo "⚠️  Dump not found: $dump_file"
    fi
done

echo "✅ Restore complete!"