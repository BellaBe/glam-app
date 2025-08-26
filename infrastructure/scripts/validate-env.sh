#!/bin/bash
# Validate environment variables for GLAM You Up

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

ENV_FILE="${1:-.env}"
ERRORS=0
WARNINGS=0

if [ ! -f "$ENV_FILE" ]; then
    error "Environment file $ENV_FILE not found"
    exit 1
fi

source "$ENV_FILE"

echo "Validating environment variables..."
echo "=================================="

# Required variables
REQUIRED_VARS=(
    "APP_ENV"
    "DOMAIN"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "CLIENT_JWT_SECRET"
    "SHOPIFY_APP_URL"
    "SHOPIFY_API_KEY"
    "SHOPIFY_API_SECRET"
    "SHOPIFY_SCOPES"
)

# Database passwords
DB_PASSWORDS=(
    "ANALYTICS_DB_PASSWORD"
    "BILLING_DB_PASSWORD"
    "CATALOG_DB_PASSWORD"
    "CREDIT_DB_PASSWORD"
    "MERCHANT_DB_PASSWORD"
    "NOTIFICATION_DB_PASSWORD"
    "SEASON_COMPATIBILITY_DB_PASSWORD"
    "SELFIE_AI_DB_PASSWORD"
    "RECOMMENDATION_DB_PASSWORD"
    "TOKEN_DB_PASSWORD"
    "WEBHOOK_DB_PASSWORD"
    "SHOPIFY_SESSION_DB_PASSWORD"
)

# Check required variables
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        error "$var is not set"
        ERRORS=$((ERRORS + 1))
    else
        log "$var is set"
    fi
done

# Check database passwords
for var in "${DB_PASSWORDS[@]}"; do
    if [ -z "${!var:-}" ]; then
        error "$var is not set"
        ERRORS=$((ERRORS + 1))
    elif [ "${!var}" == "your_${var,,}" ] || [ "${!var}" == "CHANGE_ME" ]; then
        error "$var is using default value - CHANGE IT!"
        ERRORS=$((ERRORS + 1))
    else
        log "$var is set"
    fi
done

# Check optional but recommended
if [ -z "${SMTP_HOST:-}" ]; then
    warn "SMTP_HOST not set - email notifications will not work"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
    warn "OPENAI_API_KEY not set - AI services may not work"
    WARNINGS=$((WARNINGS + 1))
fi

# Validate JWT secret strength
if [ -n "${CLIENT_JWT_SECRET:-}" ] && [ ${#CLIENT_JWT_SECRET} -lt 32 ]; then
    error "CLIENT_JWT_SECRET should be at least 32 characters"
    ERRORS=$((ERRORS + 1))
fi

echo "=================================="
if [ $ERRORS -eq 0 ]; then
    log "✅ All required variables are set!"
else
    error "❌ Found $ERRORS errors"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    warn "Found $WARNINGS warnings"
fi