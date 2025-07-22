# services/merchant-service/README.md
# Merchant Service

The Merchant Service is the single source of truth for merchant identity and lifecycle status in the GLAM platform. It manages Shopify store data, onboarding flows, and status transitions.

## Core Principles

- **Single Source of Truth**: Authoritative merchant identity and status management
- **Event-Driven Integration**: Publishes merchant state changes, listens to domain facts
- **Shopify-Native**: Deep integration with Shopify's app lifecycle
- **Multi-tenancy**: Secure merchant data isolation
- **Bounded Context**: Owns only merchant identity and status, nothing more

## Key Features

1. **Merchant Identity Management**: Store profiles, Shopify integration data
2. **Status Lifecycle**: PENDING → ONBOARDING → TRIAL/ACTIVE → SUSPENDED/DEACTIVATED
3. **Configuration Management**: Widget settings, branding, technical configuration
4. **Installation Tracking**: Platform installation/uninstallation records
5. **Activity Recording**: Fire-and-forget activity events for analytics
6. **Event Publishing**: Domain events for merchant lifecycle changes

## Architecture

- **Port**: 8013 (internal), 8113 (external development)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for frequently accessed merchant data
- **Message Bus**: NATS JetStream for event publishing
- **Framework**: FastAPI with Python 3.11+

## API Endpoints

### Core Operations
- `GET /api/v1/merchants/{merchant_id}` - Get merchant by UUID
- `GET /api/v1/merchants/lookup` - Lookup by platform-specific ID
- `GET /api/v1/merchants/{merchant_id}/config` - Get configuration
- `PATCH /api/v1/merchants/{merchant_id}/config` - Update configuration
- `POST /api/v1/merchants/{merchant_id}/activity` - Record activity

### Health & Monitoring
- `GET /api/v1/health` - Health check
- `GET /metrics` - Prometheus metrics

## Event Architecture

### Subscribed Events (React to Domain Facts)
- `evt.webhook.app.installed` - Creates merchant from Shopify installation
- `evt.webhook.app.uninstalled` - Deactivates merchant
- `evt.billing.subscription.activated` - Transitions to ACTIVE status
- `evt.billing.trial.started` - Transitions to TRIAL status
- `evt.billing.payment.retry.exhausted` - Suspends merchant
- `evt.credits.balance.exhausted` - Suspends merchant

### Published Events (Publish Intent)
- `evt.merchant.created` - New merchant created
- `evt.merchant.status.changed` - Status transition occurred
- `evt.merchant.config.updated` - Configuration updated
- `evt.merchant.activity.recorded` - Activity recorded

## Data Models

### Merchant
Core merchant profile with Shopify integration data, business identity, and onboarding status.

### MerchantStatus
Status lifecycle management with timestamps and transition history.

### MerchantConfiguration  
Widget settings, branding, technical configuration, and legal compliance.

### InstallationRecord
Platform installation/uninstallation tracking for audit and analytics.

## Development

```bash
# Setup development environment
make setup-dev

# Run tests
make test

# Format code
make format

# Start with Docker
make docker-run

# View logs
make docker-logs
```

## Configuration

Service configuration follows the three-tier hierarchy:
1. `config/shared.yml` - Common settings
2. `config/services/merchant-service.yml` - Service-specific settings  
3. `.env` - Secrets and environment variables

## Status Transitions

```
PENDING → ONBOARDING → TRIAL/ACTIVE
    ↓         ↓           ↓
DEACTIVATED ←---------← SUSPENDED
```

Valid transitions are enforced in the service layer with comprehensive event publishing for each state change.