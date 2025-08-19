#!/bin/bash
# This script validates all Prisma schemas in the project

echo "🔍 Validating Prisma schemas..."

# Check Shopify app Prisma schema
if [ -f "apps/shopify-app/prisma/schema.prisma" ]; then
    echo "Checking Shopify app schema..."
    cd apps/shopify-app || exit 1
    npx prisma validate 2>/dev/null || {
        echo "❌ Shopify app Prisma schema validation failed"
        exit 1
    }
    cd ../.. || exit 1
fi

# Check all backend service Prisma schemas
for service in services/*/prisma/schema.prisma; do
    if [ -f "$service" ]; then
        service_dir=$(dirname "$(dirname "$service")")
        service_name=$(basename "$service_dir")
        echo "Checking $service_name schema..."
        cd "$service_dir" || exit 1
        prisma validate 2>/dev/null || poetry run prisma validate 2>/dev/null || {
            echo "❌ $service_name Prisma schema validation failed"
            exit 1
        }
        cd ../.. || exit 1
    fi
done

echo "✅ All Prisma schemas are valid"
