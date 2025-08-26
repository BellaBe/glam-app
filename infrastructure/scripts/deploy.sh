#!/bin/bash
# ================================================================================
# GLAM You Up - Deploy from Laptop to Vultr
# FILE: infrastructure/scripts/deploy.sh
#
# Description: Deploy directly from your laptop to Vultr server
# Usage: ./deploy.sh [deploy|rollback|status] [version]
# Example: ./deploy.sh deploy v1.0.0
# ================================================================================

set -euo pipefail

# ================================================================================
# CONFIGURATION
# ================================================================================

# Default values (can be overridden by environment variables)
REMOTE_HOST=${REMOTE_HOST:-"your-vultr-ip"}
REMOTE_USER=${REMOTE_USER:-"deploy"}
REMOTE_DIR=${REMOTE_DIR:-"/opt/glam"}

# Action and version
ACTION=${1:-deploy}
VERSION=${2:-latest}

# Local paths
LOCAL_DIR=$(pwd)
COMPOSE_FILE="docker-compose.prod.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# ================================================================================
# PRE-DEPLOYMENT CHECKS
# ================================================================================

pre_deploy_checks() {
    log "Running pre-deployment checks..."
    
    # Check if .env.prod exists
    if [[ ! -f ".env.prod" ]]; then
        error ".env.prod not found. Create it from .env.prod.template"
        exit 1
    fi
    
    # Check SSH connection
    if ! ssh -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} "echo 'SSH OK'" &>/dev/null; then
        error "Cannot connect to ${REMOTE_USER}@${REMOTE_HOST}"
        echo "Make sure:"
        echo "  1. Server IP is correct in REMOTE_HOST"
        echo "  2. SSH key is added: ssh-copy-id ${REMOTE_USER}@${REMOTE_HOST}"
        exit 1
    fi
    
    # Check if docker-compose file exists locally
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "$COMPOSE_FILE not found in current directory"
        exit 1
    fi
    
    # Validate docker-compose file
    if ! docker-compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        error "Invalid docker-compose configuration"
        exit 1
    fi
    
    log "✅ Pre-deployment checks passed"
}

# ================================================================================
# SYNC FILES TO SERVER
# ================================================================================

sync_files() {
    log "Syncing files to server..."
    
    # Create exclude file for rsync
    cat > /tmp/rsync-exclude <<EOF
.git/
.env
.env.local
.env.dev
node_modules/
__pycache__/
*.pyc
.pytest_cache/
.coverage
*.log
.DS_Store
.vscode/
.idea/
EOF
    
    # Sync files using rsync
    rsync -avz --delete \
        --exclude-from=/tmp/rsync-exclude \
        -e "ssh -o StrictHostKeyChecking=no" \
        ./ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    
    # Copy production environment file
    scp .env.prod ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/.env
    
    rm /tmp/rsync-exclude
    log "✅ Files synced to server"
}

# ================================================================================
# BUILD IMAGES ON SERVER
# ================================================================================

build_on_server() {
    log "Building Docker images on server..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} <<EOF
        set -e
        cd ${REMOTE_DIR}
        
        echo "Building images with version: ${VERSION}"
        
        # Export version for docker-compose
        export VERSION=${VERSION}
        
        # Build all images in parallel
        docker-compose -f ${COMPOSE_FILE} build --parallel
        
        # Tag images with version
        docker-compose -f ${COMPOSE_FILE} images | tail -n +2 | awk '{print \$2}' | while read image; do
            docker tag \${image}:latest \${image}:${VERSION}
        done
EOF
    
    log "✅ Images built successfully"
}

# ================================================================================
# DEPLOY APPLICATION
# ================================================================================

deploy() {
    log "Starting deployment of version ${VERSION}..."
    
    # Run pre-deployment checks
    pre_deploy_checks
    
    # Sync files to server
    sync_files
    
    # Build images on server
    build_on_server
    
    # Deploy on server
    log "Deploying services..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} <<'REMOTE_SCRIPT'
        set -e
        cd ${REMOTE_DIR}
        
        # Create backup before deployment
        echo "Creating backup..."
        mkdir -p /var/backups/glam
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        
        # Backup databases
        for db in shopify_session_db analytics_db billing_db catalog_db credit_db merchant_db notification_db recommendation_db season_compatibility_db selfie_db token_db webhook_db; do
            docker exec glam-postgres pg_dump -U postgres -Fc $db > /var/backups/glam/${db}_${TIMESTAMP}.dump 2>/dev/null || true
        done
        
        # Stop existing containers
        echo "Stopping existing services..."
        docker-compose -f docker-compose.prod.yaml down
        
        # Start infrastructure services first
        echo "Starting infrastructure services..."
        docker-compose -f docker-compose.prod.yaml up -d postgres nats
        
        # Wait for PostgreSQL to be ready
        echo "Waiting for PostgreSQL..."
        until docker exec glam-postgres pg_isready -U postgres; do
            sleep 2
        done
        
        # Run database migrations
        echo "Running database migrations..."
        for service in analytics billing credit catalog merchant notification recommendation season-compatibility selfie token webhook; do
            echo "  Migrating ${service}-service..."
            docker-compose -f docker-compose.prod.yaml run --rm ${service}-service \
                sh -c "cd /app && prisma migrate deploy" 2>/dev/null || echo "  ⚠️  Migration skipped for ${service}"
        done
        
        # Start all services
        echo "Starting all services..."
        docker-compose -f docker-compose.prod.yaml up -d
        
        # Wait for services to be healthy
        echo "Waiting for services to become healthy..."
        sleep 15
        
        # Health check
        echo "Checking service health..."
        for service in analytics billing credit catalog merchant notification recommendation season-compatibility selfie token webhook; do
            if docker exec ${service}-service curl -sf http://localhost:8000/health >/dev/null 2>&1; then
                echo "  ✅ ${service}-service is healthy"
            else
                echo "  ⚠️  ${service}-service health check failed"
            fi
        done
        
        # Clean up old images
        docker image prune -f
        
        echo "Deployment complete!"
REMOTE_SCRIPT
    
    log "✅ Deployment completed successfully!"
    log "🌐 Application URL: https://${REMOTE_HOST}"
}

# ================================================================================
# ROLLBACK DEPLOYMENT
# ================================================================================

rollback() {
    warn "Starting rollback..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} <<'REMOTE_SCRIPT'
        set -e
        cd ${REMOTE_DIR}
        
        # Find latest backup
        LATEST_BACKUP=$(ls -t /var/backups/glam/*.dump 2>/dev/null | head -1)
        
        if [[ -z "$LATEST_BACKUP" ]]; then
            echo "❌ No backup found for rollback"
            exit 1
        fi
        
        BACKUP_TIMESTAMP=$(basename $LATEST_BACKUP | grep -oE '[0-9]{8}_[0-9]{6}' | head -1)
        echo "Rolling back to backup: $BACKUP_TIMESTAMP"
        
        # Stop all services
        docker-compose -f docker-compose.prod.yaml down
        
        # Start PostgreSQL
        docker-compose -f docker-compose.prod.yaml up -d postgres
        sleep 10
        
        # Restore databases
        for db in shopify_session_db analytics_db billing_db catalog_db credit_db merchant_db notification_db recommendation_db season_compatibility_db selfie_db token_db webhook_db; do
            BACKUP_FILE="/var/backups/glam/${db}_${BACKUP_TIMESTAMP}.dump"
            if [[ -f "$BACKUP_FILE" ]]; then
                echo "  Restoring $db..."
                docker exec -i glam-postgres pg_restore -U postgres -d $db -c < $BACKUP_FILE 2>/dev/null || true
            fi
        done
        
        # Start all services with previous version
        docker-compose -f docker-compose.prod.yaml up -d
        
        echo "Rollback complete!"
REMOTE_SCRIPT
    
    log "✅ Rollback completed"
}

# ================================================================================
# CHECK STATUS
# ================================================================================

status() {
    log "Checking deployment status on ${REMOTE_HOST}..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} <<'REMOTE_SCRIPT'
        cd ${REMOTE_DIR}
        
        echo ""
        echo "=== Service Status ==="
        docker-compose -f docker-compose.prod.yaml ps
        
        echo ""
        echo "=== Service Health ==="
        for service in analytics billing credit catalog merchant notification recommendation season-compatibility selfie token webhook; do
            if docker exec ${service}-service curl -sf http://localhost:8000/health >/dev/null 2>&1; then
                echo "  ✅ ${service}-service"
            else
                echo "  ❌ ${service}-service"
            fi
        done
        
        echo ""
        echo "=== Resource Usage ==="
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
        
        echo ""
        echo "=== Database Connections ==="
        docker exec glam-postgres psql -U postgres -c "SELECT datname, numbackends FROM pg_stat_database WHERE datname NOT IN ('template0', 'template1', 'postgres');"
REMOTE_SCRIPT
}

# ================================================================================
# VIEW LOGS
# ================================================================================

logs() {
    SERVICE=${2:-}
    if [[ -z "$SERVICE" ]]; then
        log "Tailing all service logs..."
        ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_DIR} && docker-compose -f docker-compose.prod.yaml logs -f --tail=100"
    else
        log "Tailing logs for ${SERVICE}..."
        ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_DIR} && docker-compose -f docker-compose.prod.yaml logs -f --tail=100 ${SERVICE}"
    fi
}

# ================================================================================
# QUICK DEPLOY (No Build)
# ================================================================================

quick_deploy() {
    log "Quick deploy (restart services only)..."
    
    pre_deploy_checks
    sync_files
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} <<'REMOTE_SCRIPT'
        set -e
        cd ${REMOTE_DIR}
        
        # Restart services without rebuilding
        docker-compose -f docker-compose.prod.yaml restart
        
        echo "Quick deploy complete!"
REMOTE_SCRIPT
    
    log "✅ Quick deploy completed"
}

# ================================================================================
# MAIN EXECUTION
# ================================================================================

# Show header
echo "=================================================================================="
echo "                    GLAM You Up - Deploy from Laptop"
echo "=================================================================================="
echo "Target: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
echo "Action: ${ACTION}"
echo "Version: ${VERSION}"
echo "=================================================================================="
echo ""

# Check if remote host is configured
if [[ "$REMOTE_HOST" == "your-vultr-ip" ]]; then
    error "Please configure REMOTE_HOST with your server IP"
    echo ""
    echo "Usage:"
    echo "  export REMOTE_HOST=your.server.ip"
    echo "  ./deploy.sh deploy"
    echo ""
    echo "Or edit this script and set REMOTE_HOST directly"
    exit 1
fi

# Execute action
case "$ACTION" in
    deploy)
        deploy
        ;;
    quick)
        quick_deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    logs)
        logs $@
        ;;
    *)
        echo "Usage: $0 {deploy|quick|rollback|status|logs} [version|service]"
        echo ""
        echo "Commands:"
        echo "  deploy [version]   - Full deployment with build"
        echo "  quick              - Quick restart without build"
        echo "  rollback           - Rollback to previous version"
        echo "  status             - Show deployment status"
        echo "  logs [service]     - View service logs"
        echo ""
        echo "Examples:"
        echo "  $0 deploy                    # Deploy latest"
        echo "  $0 deploy v1.0.0            # Deploy specific version"
        echo "  $0 logs                     # View all logs"
        echo "  $0 logs merchant-service    # View specific service logs"
        echo ""
        echo "Environment variables:"
        echo "  REMOTE_HOST=your.server.ip  # Server IP address"
        echo "  REMOTE_USER=deploy          # SSH user (default: deploy)"
        echo "  REMOTE_DIR=/opt/glam        # Remote directory (default: /opt/glam)"
        exit 1
        ;;
esac