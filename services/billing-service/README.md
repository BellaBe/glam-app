# Billing Service

The Billing Service manages Shopify managed app pricing, subscription states, and free trials for the GLAM platform.

## Overview

This service is the authoritative source for billing status, maintaining a clean separation between trial management and subscription management. It enables merchants to access platform features through either paid subscriptions or time-limited trials.

## Key Features

- **Managed Pricing Integration**: Works with Shopify's managed pricing system
- **Trial Management**: Independent trial system with configurable duration
- **Subscription Management**: Tracks subscription states via webhooks
- **Event-Driven Architecture**: Publishes billing state changes for other services
- **Idempotency Support**: Prevents duplicate operations
- **Dual Authentication**: Separate keys for frontend vs admin operations

## Architecture

- **Port**: 8016 (internal), 8116 (development)
- **Database**: PostgreSQL with Prisma ORM
- **Cache**: Redis for idempotency and entitlements
- **Message Bus**: NATS JetStream
- **Authentication**: Bearer token with dual-key system

## API Endpoints

### Frontend Endpoints (Bearer: BILLING_API_KEY)

- `GET /api/billing/managed/plans` - Get available plans with trial status
- `POST /api/billing/managed/redirect` - Generate Shopify checkout URL
- `POST /api/billing/trials` - Create or activate trial
- `GET /api/billing/trials/current` - Get current trial status
- `GET /api/billing/entitlements/current` - Check access entitlements
- `GET /api/billing/state` - Get complete billing state

### Admin Endpoints (Bearer: BILLING_ADMIN_API_KEY)

- `POST /internal/billing/reconcile` - Force sync with Shopify
- `POST /internal/billing/trials/extend` - Extend trial for support

## Events

### Published Events

- `evt.billing.trial.activated` - Trial started
- `evt.billing.trial.expired` - Trial ended
- `evt.billing.subscription.changed` - Any subscription change
- `evt.billing.subscription.activated` - First activation
- `evt.billing.subscription.cancelled` - Cancellation
- `evt.billing.credits.grant` - One-time purchase credits

### Consumed Events

- `evt.webhook.app.subscription_updated` - Shopify subscription webhooks
- `evt.webhook.app.purchase_updated` - One-time purchase webhooks
- `evt.webhook.app.uninstalled` - App uninstall events

## Configuration

Required environment variables:

```env
# Authentication Keys
BILLING_API_KEY=your-frontend-key
BILLING_ADMIN_API_KEY=your-admin-key

# Shopify Configuration
APP_HANDLE=your-app-handle
SHOPIFY_MANAGED_CHECKOUT_BASE=https://checkout-base-url
ALLOWED_RETURN_DOMAINS=domain1.com,domain2.com

# Trial Settings
DEFAULT_TRIAL_DAYS=14
TRIAL_GRACE_HOURS=0

# Cache TTLs
IDEMPOTENCY_TTL_HOURS=24
ENTITLEMENTS_CACHE_TTL_SECONDS=30
```

## Business Rules

1. **Trial Independence**: Trials are separate from subscriptions
2. **One Trial Per Merchant**: Once consumed, trials cannot be reused
3. **Domain Validation**: All domains must be *.myshopify.com format
4. **Webhook Deduplication**: Uses both Redis and database for deduplication
5. **Entitlement Sources**: Access granted via subscription OR trial
6. **Trial Expiry**: Hourly job marks expired trials

## Development

### Setup

```bash
# Install dependencies
poetry install

# Generate Prisma client
prisma generate

# Run migrations
prisma migrate dev

# Start service
make dev
```

### Testing

```bash
# Run tests
make test

# Run with coverage
make test-coverage
```

## Integration Points

### Services That Consume Billing Events

- **Merchant Service**: Updates merchant billing status
- **Credit Service**: Processes credit grants and trial events
- **Catalog Service**: Checks entitlements before operations
- **Analytics Service**: Tracks billing metrics
- **Email Scheduler**: Sends billing-related emails

## ID Management

- **correlation_id**: Propagated throughout the billing flow
- **event_id**: Unique for each published event
- **idempotency_key**: Used for trial creation and redirects

## Error Handling

Common error codes:

- `INVALID_DOMAIN` (400): Non-myshopify.com domain
- `INVALID_PLAN` (400): Unknown plan ID
- `TRIAL_ALREADY_USED` (409): Trial consumed
- `SUBSCRIPTION_EXISTS` (409): Already subscribed

## Monitoring

Key metrics:

- `billing_trial_started_total` - Trial activations
- `billing_subscription_transitions_total` - Status changes
- `billing_active_subscriptions` - Current active subs by plan
- `billing_webhook_duplicate_total` - Deduped webhooks
