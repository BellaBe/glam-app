
# services/webhook-service/README.md
# Webhook Service

The Webhook Service receives and processes webhooks from external platforms (initially Shopify). It validates webhook authenticity using HMAC with support for secret rotation, ensures idempotent processing with 72-hour deduplication, and asynchronously transforms platform-specific events into domain events.

## Overview

- **Port**: 8012 (internal), 8112 (external development)
- **Purpose**: Receive webhooks, validate authenticity, and publish domain events
- **Architecture**: Event-driven, async processing, pure receive-only

## Key Features

- **HMAC Validation**: Dual-secret support for zero-downtime rotation
- **Idempotency**: 72-hour deduplication using Redis
- **Async Processing**: ACK immediately, process in background
- **Event Translation**: Convert platform webhooks to domain events
- **Production Ready**: Comprehensive metrics and health checks

## API Endpoints

### Webhook Reception
```
POST /api/v1/shopify/webhooks/{topic-path}
Headers:
  - X-Shopify-Hmac-Sha256: HMAC signature
  - X-Shopify-Topic: Event type (e.g., orders/create)
  - X-Shopify-Shop-Domain: Shop domain
  - X-Shopify-Webhook-Id: Unique webhook ID
  - X-Shopify-Api-Version: API version (optional)
  - Content-Type: application/json (required)

Response: {"success": true, "webhook_id": "uuid"}
```

### Health Checks
```
GET /api/v1/health          - Basic health check
GET /api/v1/health/detailed - Detailed component status
GET /metrics               - Prometheus metrics
```

## Domain Events Published

| Event | Description |
|-------|-------------|
| `evt.webhook.app.uninstalled` | App removed from shop |
| `evt.webhook.app.subscription_updated` | Subscription changed |
| `evt.webhook.app.purchase_updated` | One-time purchase |
| `evt.webhook.order.created` | New order placed |
| `evt.webhook.catalog.product_*` | Product changes |
| `evt.webhook.catalog.collection_*` | Collection changes |
| `evt.webhook.inventory.updated` | Inventory level changes |
| `evt.webhook.gdpr.data_request` | GDPR data export request |
| `evt.webhook.gdpr.customer_redact` | GDPR customer data removal |
| `evt.webhook.gdpr.shop_redact` | GDPR shop data removal |

## Configuration

The service uses a three-tier configuration hierarchy:

1. **Shared Configuration** (`config/shared.yml`)
2. **Service Configuration** (`config/services/webhook-service.yml`)
3. **Environment Variables** (`.env` - secrets only)

### Key Configuration Options

```yaml
webhook:
  body_limit_bytes: 2097152  # 2MB
  idempotency_ttl_seconds: 259200  # 72 hours
  max_retries: 10
  ip_allowlist_mode: disabled  # disabled/soft/hard
  shopify_ips: []  # List of allowed IPs
```

### Environment Variables

```bash
# Required
SHOPIFY_API_SECRET=your-primary-webhook-secret
DATABASE_URL=postgresql://webhook:password@localhost:5412/webhook_db

# Optional
SHOPIFY_API_SECRET_NEXT=your-rotation-secret  # For secret rotation
```

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
poetry run python -m src.main
```

### Docker Compose

```bash
# Start all dependencies
docker-compose up -d

# View logs
docker-compose logs -f webhook-service

# Stop services
docker-compose down
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test
poetry run pytest tests/unit/test_webhook_service.py -v
```

### Manual Testing

Use the provided test script:

```bash
poetry run python scripts/test_webhook.py
```

## Webhook Processing Flow

1. **Receive Request**: POST to `/api/v1/shopify/webhooks/{topic}`
2. **Validate Content-Type**: Must be `application/json`
3. **Read Body**: With 2MB size limit
4. **Extract Headers**: Case-insensitive, canonical storage
5. **Validate HMAC**: Try primary secret, then rotation secret
6. **Check Idempotency**: Redis lookup with 72h TTL
7. **Parse JSON**: Validate payload structure
8. **Store Webhook**: Database with fallback to stream
9. **Publish to Queue**: For async processing
10. **Return 200 OK**: Within 5 seconds

## Security

### HMAC Validation

The service validates webhook authenticity using HMAC-SHA256:

```python
# Primary secret validation
hmac_sha256(primary_secret, raw_body) == header_hmac

# Rotation secret validation (if configured)
hmac_sha256(rotation_secret, raw_body) == header_hmac
```

### Secret Rotation

Zero-downtime secret rotation:

1. Configure `SHOPIFY_API_SECRET_NEXT` with new secret
2. Monitor metrics for rotation secret usage
3. Update Shopify to use new secret
4. Move new secret to `SHOPIFY_API_SECRET`
5. Remove `SHOPIFY_API_SECRET_NEXT`

### IP Allowlist

Three modes available:

- **disabled**: No IP checking (default)
- **soft**: Log non-Shopify IPs but accept
- **hard**: Reject non-Shopify IPs with 403

## Metrics

### Counters

- `webhook_received_total{platform,topic_enum}` - Successfully received
- `webhook_processed_total{platform,topic_enum}` - Successfully processed
- `webhook_duplicate_total{platform,topic_enum}` - Idempotent duplicates
- `webhook_invalid_hmac_total{platform}` - HMAC failures
- `webhook_hmac_rotation_used_total{platform}` - Rotation secret used

### Histograms

- `webhook_ack_latency_seconds{platform,topic_enum}` - Time to ACK
- `webhook_processing_duration_seconds{topic_enum}` - Processing time
- `webhook_payload_size_bytes{platform,topic_enum}` - Payload sizes

## Error Handling

| Error | HTTP Status | Retriable | Description |
|-------|-------------|-----------|-------------|
| `INVALID_CONTENT_TYPE` | 400 | No | Wrong content type |
| `PAYLOAD_TOO_LARGE` | 413 | No | Exceeds 2MB limit |
| `INVALID_SIGNATURE` | 401 | No | HMAC validation failed |
| `DUPLICATE_WEBHOOK` | 200 | No | Already processed |
| `MISSING_HEADERS` | 400 | No | Required headers missing |
| `DOMAIN_MISMATCH` | 400 | No | Shop domain mismatch |
| `MALFORMED_PAYLOAD` | 422 | No | Invalid JSON |
| `IP_NOT_ALLOWED` | 403 | No | IP allowlist rejection |

## Monitoring

### Health Checks

The detailed health endpoint provides:

- Database connectivity
- Redis connectivity
- NATS messaging status
- Secret rotation warnings

### Alerting Recommendations

1. **High HMAC Failures**: > 10/minute might indicate attack
2. **Secret Rotation Usage**: Monitor when transitioning secrets
3. **Processing Failures**: > 5% failure rate
4. **Queue Depth**: > 1000 pending webhooks
5. **Latency**: ACK time > 2 seconds

## Troubleshooting

### Common Issues

1. **HMAC Validation Failures**
   - Check secret configuration
   - Ensure raw body bytes are used
   - Verify no middleware is modifying body

2. **Duplicate Webhooks**
   - Normal behavior - returns 200 OK
   - Check Redis connectivity
   - Verify TTL configuration

3. **Processing Delays**
   - Check NATS connectivity
   - Monitor worker health
   - Review queue depth metrics

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG poetry run python -m src.main
```

## Architecture Notes

- **Receive-Only**: No external API calls
- **Async Processing**: Immediate ACK, background processing
- **Event Sourcing**: All webhooks stored for audit
- **Idempotent**: Safe to retry webhook delivery
- **Scalable**: Horizontal scaling supported

## Future Enhancements

1. **Multi-Platform Support**: Extend beyond Shopify
2. **Webhook Replay**: Reprocess historical webhooks
3. **Circuit Breaker**: For downstream services
4. **Rate Limiting**: Per-shop webhook limits
5. **Webhook Signatures**: Support multiple signature methods
