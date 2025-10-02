#!/bin/bash
# scripts/health-check.sh
# Health check script for all GLAM services

set -e

echo "==================================="
echo "GLAM Platform Health Check"
echo "Time: $(date)"
echo "==================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    exit 1
fi

# Services to check
SERVICES=(
    "glam_nginx:80:/health"
    "glam_remix_bff:3000:/health"
    "glam_merchant_service:8013:/health"
    "glam_billing_service:8016:/health"
    "glam_credit_service:8015:/health"
    "glam_catalog_service:8014:/health"
    "glam_webhook_service:8012:/health"
    "glam_notification_service:8000:/health"
    "glam_token_service:8021:/health"
    "glam_selfie_service:8026:/health"
    "glam_platform_connector:8019:/health"
    "glam_recommendation_service:8025:/health"
)

echo ""
echo "Service Health Status:"
echo "----------------------"

FAILED=0

for service_info in "${SERVICES[@]}"; do
    IFS=':' read -r container port endpoint <<< "$service_info"
    
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        if docker exec "${container}" wget -q -O - "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
            echo "✅ ${container}: Healthy"
        else
            echo "⚠️  ${container}: Unhealthy (endpoint not responding)"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "❌ ${container}: Not running"
        FAILED=$((FAILED + 1))
    fi
done

# Check PostgreSQL
echo ""
echo "Database Status:"
echo "----------------"
if docker exec glam_postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Ready"
    
    # Check database sizes
    docker exec glam_postgres psql -U postgres -c "
        SELECT datname as database, 
               pg_size_pretty(pg_database_size(datname)) as size 
        FROM pg_database 
        WHERE datname NOT IN ('postgres', 'template0', 'template1')
        ORDER BY pg_database_size(datname) DESC;" 2>/dev/null
else
    echo "❌ PostgreSQL: Not ready"
    FAILED=$((FAILED + 1))
fi

# Check NATS
echo ""
echo "Message Bus Status:"
echo "-------------------"
if docker exec glam_nats wget -q -O - "http://localhost:8222/healthz" > /dev/null 2>&1; then
    echo "✅ NATS: Healthy"
else
    echo "❌ NATS: Not healthy"
    FAILED=$((FAILED + 1))
fi

# Check disk usage
echo ""
echo "System Resources:"
echo "-----------------"
df -h / | tail -n 1
echo ""
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "==================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ All systems operational"
else
    echo "⚠️  ${FAILED} service(s) need attention"
fi
echo "==================================="

exit $FAILED