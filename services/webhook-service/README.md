# Webhook Service

Unified webhook ingestion service for the GlamYouUp platform.

## Features

- **Multi-source Support**: Currently supports Shopify and Stripe webhooks
- **HMAC Signature Validation**: Secure webhook authentication
- **Idempotency**: Redis-based deduplication with configurable TTL
- **Event Mapping**: Maps external webhooks to internal domain events
- **Circuit Breakers**: Protects downstream services from cascading failures
- **Dead Letter Queue**: Failed webhooks can be replayed
- **Observability**: Structured logging, Prometheus metrics, health checks
- **Extensible**: Easy to add new webhook sources

## Architecture
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ External        │────▶│ Webhook Service  │────▶│ Event Bus       │
│ Platforms       │     │                  │     │ (NATS)          │
└─────────────────┘     └──────────────────┘     └─────────────────┘
│
▼
┌──────────────────┐
│ PostgreSQL       │
│ Redis            │
└──────────────────┘


### Service Type
- **Type**: API Service
- **Port**: 8012
- **Database**: PostgreSQL (dedicated schema)
- **Cache**: Redis for deduplication and circuit breakers
- **Messaging**: NATS JetStream for event publishing

### Key Components

1. **Webhook Handlers**
   - Shopify: Full support for products, orders, inventory, app lifecycle
   - Stripe: Payment and subscription events
   - Extensible base handler for new sources

2. **Authentication**
   - HMAC-SHA256 validation for Shopify
   - Stripe signature validation
   - Per-source secret management

3. **Deduplication**
   - Redis-based with configurable TTL (default 24h)
   - Idempotency keys based on webhook ID or content hash

4. **Circuit Breakers**
   - Per-subject breakers with sliding window
   - Automatic recovery with half-open state
   - Configurable thresholds and timeouts

5. **Event Publishing**
   - Maps webhooks to domain events
   - Publishes to appropriate NATS streams
   - Maintains correlation IDs

## API Endpoints

### Webhooks
- `POST /api/v1/webhooks/shopify/{topic}` - Shopify webhook (topic in path)
- `POST /api/v1/webhooks/shopify` - Shopify webhook (topic in header)
- `POST /api/v1/webhooks/stripe` - Stripe webhook
- `POST /api/v1/webhooks/{source}` - Generic webhook (future)

### Health
- `GET /api/v1/health` - Comprehensive health check
- `GET /api/v1/health/ready` - Kubernetes readiness
- `GET /api/v1/health/live` - Kubernetes liveness

## Environment Variables

See `.env.example` for all configuration options. Key variables:

- `SHOPIFY_WEBHOOK_SECRET` - Required for Shopify webhooks
- `STRIPE_WEBHOOK_SECRET` - Required for Stripe webhooks
- `REDIS_URL` - Redis connection for deduplication
- `DEDUP_TTL_HOURS` - Deduplication window (default 24)
- `MAX_PAYLOAD_SIZE_MB` - Maximum webhook size (default 10)

## Development

```bash
# Install dependencies
poetry install

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start service
uvicorn src.main:app --reload --port 8012

# Run tests
pytest

# Test webhook
python scripts/test_webhook.py