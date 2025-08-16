# Billing Service

## Overview
The Billing Service manages trials and credit pack purchases for the GlamYouUp platform. It maintains minimal billing state while delegating actual payment processing to platform providers (Shopify, Stripe, etc.).

## Core Responsibilities
- Trial management and activation
- Credit pack purchase coordination
- Billing record maintenance
- Event publishing for billing activities

## Architecture
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with Prisma ORM
- **Cache**: Redis for idempotency
- **Messaging**: NATS JetStream
- **Port**: 8016 (internal), 8116 (development)

## API Endpoints

### Trials
- `POST /api/billing/trials` - Activate trial
- `GET /api/billing/trials` - Get trial status

### Purchases
- `POST /api/billing/purchases` - Create credit purchase
- `GET /api/billing/purchases` - List purchases
- `GET /api/billing/purchases/{id}` - Get single purchase

### Billing
- `GET /api/billing` - Get overall billing status

### Health
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Events

### Published Events
- `evt.billing.trial.started` - Trial activated
- `evt.billing.trial.expired` - Trial ended
- `evt.billing.credits.purchased` - Purchase completed

### Consumed Events
- `evt.merchant.created` - Create billing record
- `evt.webhook.app.purchase_updated` - Process purchase webhook

## Configuration

### Credit Packs
- **Small**: 100 credits for $9.99
- **Medium**: 500 credits for $39.99
- **Large**: 1000 credits for $69.99

### Trial Settings
- Duration: 14 days
- Credits: 500

## Development Setup

1. Install dependencies:
```bash
cd services/billing-service
poetry install
```

2. Set up environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
prisma migrate dev
```

4. Start the service:
```bash
poetry run python src/main.py
```

## Testing

```bash
# Unit tests
poetry run pytest tests/unit -v

# Integration tests
poetry run pytest tests/integration -v

# All tests with coverage
poetry run pytest --cov=src --cov-report=html
```

## Docker

```bash
# Build image
docker build -t billing-service -f Dockerfile ../..

# Run container
docker run -p 8116:8000 --env-file .env billing-service
```

## Error Codes
- `TRIAL_ALREADY_USED` (409) - Trial has been activated
- `INVALID_PACK` (400) - Invalid credit pack selected
- `MERCHANT_NOT_FOUND` (404) - Merchant not found
- `PURCHASE_NOT_FOUND` (404) - Purchase not found
- `PLATFORM_ERROR` (502) - Platform checkout failed

## Dependencies on Other Services
- **Merchant Service**: Listens for merchant creation events
- **Webhook Service**: Listens for purchase webhook events
- **Credit Service**: Publishes events for credit allocation
- **Analytics Service**: Publishes events for tracking
- **Notification Service**: Publishes events for emails

## Monitoring
- Health endpoint: `/health`
- Metrics endpoint: `/metrics`
- Logs: Structured JSON logging with correlation IDs

## Security
- JWT authentication required for all endpoints except health
- Platform validation via headers
- Idempotency keys for critical operations
- Redis-based deduplication

## Maintenance

### Daily Cron Jobs
- Check and expire trials
- Expire pending purchases

### Cleanup Tasks
- Remove expired idempotency keys (24h TTL)
- Archive old purchase records (90 days)

## Contact
Team: GlamYouUp Platform Team
Slack: #platform-billing
