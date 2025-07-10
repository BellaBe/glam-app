Credit management service for merchant credits and plugin access control. This service manages credit balances, handles credit transactions, and provides real-time plugin status based on credit availability.

## Features

- **Credit Account Management**: Automatic account creation with trial credits
- **Transaction Processing**: Handle order payments, refunds, and manual adjustments
- **Plugin Status API**: Real-time plugin enable/disable based on credit balance
- **Event-Driven Architecture**: NATS JetStream integration for reliable messaging
- **Audit Trail**: Complete transaction history with idempotency
- **Balance Monitoring**: Automatic threshold detection and notifications
- **Caching**: Redis-based caching for high-performance plugin status checks
- **Metrics**: Prometheus metrics for monitoring and alerting

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
   cd services/credit-service
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
   poetry run uvicorn src.main:app --reload --port 8015
   ```

### Docker Setup

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Check health**:
   ```bash
   curl http://localhost:8015/api/v1/health
   ```

### Testing

1. **Run tests**:
   ```bash
   poetry run pytest
   ```

2. **Test API manually**:
   ```bash
   python scripts/test_credit.py
   ```

## API Documentation

### Plugin Status
- `GET /api/v1/credits/plugin-status/{merchant_id}` - Check plugin status

### Accounts
- `GET /api/v1/credits/accounts/{merchant_id}` - Get account details
- `GET /api/v1/credits/accounts/{merchant_id}/balance` - Quick balance check

### Transactions
- `GET /api/v1/credits/transactions` - Transaction history with pagination
- `GET /api/v1/credits/transactions/{transaction_id}` - Get specific transaction

### Health & Monitoring
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health with component status
- `GET /metrics` - Prometheus metrics

## Event Architecture

### Subscribes To
- `evt.shopify.webhook.order_paid` - Add credits for orders
- `evt.shopify.webhook.order_refunded` - Refund credits
- `evt.billing.payment_succeeded` - Add credits for billing
- `evt.merchant.created` - Create account with trial credits
- `evt.credits.manual_adjustment` - Manual admin adjustments

### Publishes
- `evt.credits.recharged` - Credits added
- `evt.credits.refunded` - Credits refunded
- `evt.credits.adjusted` - Manual adjustment
- `evt.credits.low_balance_reached` - Balance below threshold
- `evt.credits.balance_restored` - Balance above threshold
- `evt.credits.balance_exhausted` - Balance reached zero
- `evt.credits.plugin_status_changed` - Plugin status changed

## Configuration

Key environment variables:

```bash
# Service
SERVICE_PORT=8015
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://credit:password@localhost:5432/credit_db

# Redis
REDIS_URL=redis://localhost:6379

# NATS
NATS_URL=nats://localhost:4222

# Credits
TRIAL_CREDITS=100
ORDER_CREDIT_FIXED_AMOUNT=10
LOW_BALANCE_THRESHOLD_PERCENT=20

# Plugin Status
PLUGIN_STATUS_CACHE_TTL=15

## Monitoring

### Metrics
- `credits_balance_total{merchant_id}` - Current balances
- `credits_transactions_total{type,reference_type}` - Transaction counts
- `credits_plugin_status_checks_total{status}` - Plugin status checks
- `credits_events_published_total{event_type}` - Published events

### Health Checks
- Database connectivity
- Redis connectivity
- NATS connectivity
- Component status

## Architecture

The service follows microservice patterns with:

- **Event-Driven Design**: All modifications through events
- **Read-Only API**: Public APIs only for queries
- **Repository Pattern**: Data access abstraction
- **Domain Services**: Business logic separation
- **Caching Layer**: Redis for performance
- **Monitoring**: Comprehensive observability

## Development

### Code Style
- **Linting**: Pylance (strict mode)
- **Formatting**: Black (100 char line length)
- **Type Checking**: MyPy with strict settings
- **Import Sorting**: isort

### Database
- **ORM**: SQLAlchemy with mapped API
- **Migrations**: Alembic
- **Connection**: Async with connection pooling

### Testing
- **Framework**: Pytest with async support
- **Coverage**: pytest-cov
- **Integration**: Testcontainers for dependencies

## License

Copyright © 2025 GlamYouUp. All rights reserved.