# services/billing-service/README.md
"""
# Billing Service

Subscription lifecycle, payment processing, and billing coordination for the GLAM platform.

## Features

- **Subscription Management**: Create, activate, cancel subscriptions via Shopify
- **One-Time Purchases**: Credit purchases with Shopify billing
- **Trial Management**: Trial period tracking and extensions
- **Event-Driven**: Coordinates billing through domain events
- **Shopify Integration**: Deep integration with Shopify's billing APIs
- **Payment Processing**: Handles webhook events for payment completion

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Docker & Docker Compose
- PostgreSQL
- Redis
- NATS JetStream

### Development Setup

1. **Clone and setup**:
   ```bash
   cd services/billing-service
   poetry install
   cp .env.example .env
   ```

2. **Start dependencies**:
   ```bash
   docker-compose up -d postgres redis nats
   ```

3. **Run migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

4. **Start the service**:
   ```bash
   poetry run uvicorn src.main:app --reload --port 8016
   ```

### Docker Setup

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Check health**:
   ```bash
   curl http://localhost:8016/api/v1/health
   ```

## API Documentation

### Subscriptions
- `POST /api/v1/billing/subscriptions` - Create subscription
- `GET /api/v1/billing/subscriptions/{id}` - Get subscription
- `GET /api/v1/billing/subscriptions/merchant/{merchant_id}` - List merchant subscriptions
- `DELETE /api/v1/billing/subscriptions/{id}` - Cancel subscription

### One-Time Purchases
- `POST /api/v1/billing/purchases` - Create purchase
- `GET /api/v1/billing/purchases/{id}` - Get purchase
- `GET /api/v1/billing/purchases/merchant/{merchant_id}` - List merchant purchases

### Trial Management
- `GET /api/v1/billing/trial/{merchant_id}` - Get trial status
- `POST /api/v1/billing/trial/{merchant_id}/extend` - Extend trial (admin)

### Billing Plans
- `GET /api/v1/billing/plans` - List available plans
- `GET /api/v1/billing/plans/{plan_id}` - Get plan details

## Event Architecture

### Subscribes To
- `evt.webhook.app.subscription_updated` - Payment completion
- `evt.webhook.app.purchase_updated` - Purchase completion
- `evt.webhook.app.uninstalled` - App uninstallation

### Publishes
- `evt.billing.subscription.created` - Subscription created
- `evt.billing.subscription.activated` - Subscription activated
- `evt.billing.purchase.completed` - Purchase completed
- `evt.billing.trial.extended` - Trial extended
- `evt.billing.notification.*` - Notification triggers

## Configuration

Key environment variables:

- `BILLING_SERVICE_SHOPIFY_API_KEY` - Shopify API key
- `BILLING_SERVICE_SHOPIFY_API_SECRET` - Shopify API secret
- `BILLING_SERVICE_DB_*` - Database configuration
- `REDIS_URL` - Redis connection
- `NATS_URL` - NATS connection

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy src/

# Linting
poetry run ruff check src/
```

## Architecture

The service follows microservice patterns with:

- **Event-Driven Design**: All coordination through events
- **Shopify-Native**: Deep Shopify billing API integration
- **Repository Pattern**: Data access abstraction
- **Domain Services**: Business logic separation
- **Return URL Flow**: Proper Shopify payment flow handling

## License

Copyright © 2025 GlamYouUp. All rights reserved.