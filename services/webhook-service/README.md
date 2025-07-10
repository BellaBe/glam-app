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



Key Components Created:
1. Core Structure

Complete directory structure matching the notification service pattern
Service lifecycle management with proper startup/shutdown
Event-driven architecture with NATS JetStream
Repository pattern using SQLAlchemy's latest mapped API

2. Models & Database

WebhookEntry - Stores all received webhooks for audit/replay
PlatformConfiguration - Manages webhook secrets per source
Uses shared mixins (TimestampedMixin, ShopMixin)
Alembic migrations setup

3. Services

WebhookService - Main orchestration service
AuthService - HMAC validation for Shopify/Stripe
DeduplicationService - Redis-based idempotency
CircuitBreakerService - Downstream protection

4. Event Handling

WebhookEventPublisher - Publishes webhook events
Maps external webhooks to domain events
Maintains event context and correlation IDs

5. Webhook Handlers

ShopifyWebhookHandler - Handles all Shopify topics
StripeWebhookHandler - Handles Stripe events
Extensible base handler for new sources

6. API Endpoints

/api/v1/webhooks/shopify/{topic} - Shopify webhooks
/api/v1/webhooks/stripe - Stripe webhooks
Comprehensive health checks

7. Production Features

Docker multi-stage build
Environment-based configuration
Structured logging with correlation IDs
Prometheus metrics
Circuit breakers with sliding windows
Dead letter queue support

Key Design Patterns Followed:

Dependency Injection - FastAPI dependencies matching notification service
Repository Pattern - Generic repository with specific implementations
Event Publishing - Domain event publisher with typed payloads
Service Lifecycle - Centralized startup/shutdown management
Error Handling - Shared error classes from the shared package

The service is production-ready and maintains complete consistency with the existing platform architecture. It can handle high-throughput webhook processing with proper deduplication, circuit breaking, and observability.