# Catalog Service

Orchestrates catalog synchronization between merchant stores and the GLAM platform.

## Overview

The Catalog Service manages the initial full catalog sync workflow, tracks synchronization progress, and coordinates with Platform Connector for data retrieval and Catalog-AI-Analysis for image processing.

## Key Features

- **Sync Orchestration**: Manages full catalog synchronization workflow
- **Progress Tracking**: Real-time visibility into sync and analysis status
- **Event-Driven**: All internal communication via events
- **State Caching**: Maintains cached merchant settings and billing entitlements
- **Idempotent Operations**: Safe retry handling for all operations

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/catalog/sync/allowed` | Check if sync is allowed |
| POST | `/api/catalog/sync` | Start new sync |
| GET | `/api/catalog/sync/status` | Get current sync status |
| GET | `/api/catalog/sync/:syncId` | Get sync job details |

## Event Subscriptions

Consumes:
- `evt.merchant.settings.updated` - Cache merchant consent flags
- `evt.billing.entitlements.changed` - Cache billing status
- `evt.connector.shopify.catalog.counted` - Set total counts
- `evt.connector.shopify.catalog.item` - Process catalog items
- `evt.analysis.completed` - Track analysis completion

Publishes:
- `evt.catalog.sync.requested` - Trigger catalog export
- `evt.catalog.analysis.requested` - Request image analysis
- `evt.catalog.sync.started` - Sync begins
- `evt.catalog.sync.progress` - Progress updates
- `evt.catalog.sync.completed` - Sync finished

## Configuration

Port: 8018 (internal), 8118 (external)

Key settings:
- `cache.ttl_settings`: 30s (merchant settings cache TTL)
- `cache.ttl_entitlements`: 30s (billing cache TTL)

## Development

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

## Testing

```bash
# Run tests
make test

# Integration tests
make test-integration
```

# ================================================================
