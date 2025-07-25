# GLAM Shared Package

Shared utilities and infrastructure components for GLAM microservices platform.

## Features

- **Standardized API Responses**: Consistent response format across all services
- **Database Integration**: SQLAlchemy models, repository pattern, and session management  
- **Event-Driven Architecture**: Publishers, subscribers, and event context management
- **Error Handling**: Comprehensive error hierarchy with automatic mapping
- **Distributed Tracing**: Correlation IDs and trace context propagation
- **Metrics & Monitoring**: Prometheus metrics with automatic HTTP tracking
- **Structured Logging**: Service-aware logging with request context
- **Configuration Management**: YAML configuration with environment overrides
- **NATS Messaging**: JetStream integration with dependency injection

## Quick Start

### Installation

```bash
# Add to your service
cd your-service/
poetry add ../shared

# Or if published to registry
poetry add glam-shared
```

### Basic Service Setup

```python
# src/main.py
from fastapi import FastAPI
from shared.api import setup_middleware, create_health_router
from shared.utils.logger import create_logger

# Create logger and app
logger = create_logger("your-service")
app = FastAPI(title="Your Service")

# Setup essential middleware
setup_middleware(app, service_name="your-service")

# Add health endpoint
app.include_router(create_health_router("your-service"), prefix="/api/v1")
```

### Configuration

```yaml
# config/services/your-service.yml
database:
  host: "localhost"
  port: 5432
  name: "your_service_db"
  user: "postgres"
  password: "password"

nats:
  servers: ["nats://localhost:4222"]
```

## Core Components

### API Module
- **Middleware**: Automatic request/response handling, tracing, metrics
- **Dependencies**: Pagination, request context, correlation IDs
- **Responses**: Standardized success, error, and paginated responses
- **Health Checks**: Built-in health endpoints

### Database Module
- **Base Models**: Async SQLAlchemy with automatic mixins
- **Repository Pattern**: Generic CRUD operations with extensibility
- **Session Management**: Async session handling with proper cleanup
- **Migrations**: Alembic integration utilities

### Event System
- **Publishers**: Domain-specific event publishing with validation
- **Subscribers**: Event processing with dependency injection
- **Context Management**: Correlation and trace propagation
- **Pre-built Events**: Common event types (notifications, billing, etc.)

### Error Handling
- **Error Hierarchy**: Structured domain and infrastructure errors
- **Automatic Mapping**: Convert external exceptions to domain errors
- **Service-Specific**: Ready-to-use errors for common domains
- **API Integration**: Automatic error response formatting

### Messaging (NATS)
- **JetStream Wrapper**: Simplified publisher/subscriber setup
- **Dependency Injection**: Service dependencies for event handlers
- **Stream Management**: Automatic stream creation and configuration
- **Health Monitoring**: Connection health checks

## Available Mixins & Base Classes

### Database Mixins
```python
# Automatic timestamps
class TimestampedMixin:
    created_at: Mapped[datetime]  # Auto-set
    updated_at: Mapped[datetime]  # Auto-updated

# Multi-tenant support  
class MerchantMixin:
    merchant_id: Mapped[UUID]      # Indexed
    merchant_domain: Mapped[str]   # Indexed

# Soft delete support
class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None]
    is_deleted: Mapped[bool]       # Indexed
```

### Repository Base
```python
class Repository(Generic[T]):
    # Available methods (all async)
    async def save(self, instance: T) -> T
    async def find_by_id(self, id: UUID) -> T | None  
    async def find_all(self, **filters) -> list[T]
    async def delete_by_id(self, id: UUID) -> None
    # Override for custom queries
```

### Event Base Classes
```python
class DomainEventPublisher:
    # Set these properties
    domain_stream: Streams = Streams.YOUR_DOMAIN
    service_name_override: str = "your-service"
    
    # Available methods
    async def publish_event(subject: str, payload: dict) -> str
    async def publish_command(command_type: str, payload: dict) -> str

class DomainEventSubscriber:
    # Must implement
    async def on_event(self, event: dict, headers: dict) -> None
    
    # Available methods  
    def get_dependency(self, key: str) -> Any
```

## Error Types

### Common Domain Errors (Ready to Use)
- `NotFoundError` - Resource not found (404)
- `ValidationError` - Invalid input (422)
- `ConflictError` - Resource conflicts (409)
- `UnauthorizedError` - Authentication required (401)
- `ForbiddenError` - Insufficient permissions (403)

### Infrastructure Errors (Ready to Use)
- `DatabaseError` - Database operation failed
- `UpstreamServiceError` - External service failure
- `MessageBusError` - NATS/messaging failure
- `S3Error` - Storage operation failed

### Service-Specific Collections
```python
# Import pre-built error collections
from shared.errors import (
    # Catalog errors
    SyncInProgressError, ItemNotFoundError,
    
    # Profile errors  
    ProfileNotFoundError, ProfileAlreadyExistsError,
    
    # Notification errors
    TemplateNotFoundError, EmailProviderError
)
```

## Event Streams

Each service publishes to designated streams:

```python
# Available streams
Streams.CATALOG      # catalog-service, catalog-connector
Streams.MERCHANT     # merchant-service
Streams.BILLING      # billing-service  
Streams.CREDIT       # credit-service
Streams.PROFILE      # profile-service
Streams.NOTIFICATION # notification-service
Streams.AI_PROCESSING # AI services
Streams.WEBHOOKS     # webhook-service
Streams.SCHEDULER    # scheduler-service
Streams.ANALYTICS    # analytics-service
```

## Configuration

### Environment Variables

All services support these patterns:

```bash
# Database
{SERVICE}_DB_HOST=localhost
{SERVICE}_DB_PORT=5432
{SERVICE}_DB_NAME=service_db
{SERVICE}_DB_USER=postgres
{SERVICE}_DB_PASSWORD=password

# Messaging  
{SERVICE}_NATS_SERVERS=nats://localhost:4222

# Logging
{SERVICE}_LOG_LEVEL=INFO
APP_ENV=dev  # dev, staging, prod
```

### YAML Configuration
```yaml
# config/services/your-service.yml
service:
  name: "your-service"
  port: 8080

database:
  host: "localhost"
  port: 5432
  name: "your_service_db"

nats:
  servers: ["nats://localhost:4222"]
```

## Development

### Testing
```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=shared
```

### Code Quality
```bash
# Format code
poetry run black .
poetry run isort .

# Type checking  
poetry run mypy shared/

# Linting
poetry run ruff check shared/
```

### Documentation
```bash
# Generate API docs
poetry run pdoc shared --html
```

## Monitoring & Observability

### Built-in Metrics (Automatic)
- `http_requests_total` - Request counts by service/endpoint/status
- `http_request_duration_seconds` - Request timing histograms  
- `http_requests_in_progress` - Active request gauge

### Health Checks (Automatic)
- `GET /api/v1/health` - Service health with timestamp
- `GET /metrics` - Prometheus metrics endpoint

### Logging Features
- **Structured Logging**: JSON in production, console in development
- **Request Context**: Automatic request_id, correlation_id
- **File Rotation**: Automatic log rotation in production
- **Environment-Aware**: Different formats per environment

## Architecture Patterns

The shared package enforces consistent patterns across services:

- **Event-Driven Design**: All inter-service communication through events
- **Repository Pattern**: Standardized data access with extensibility
- **Dependency Injection**: Clean service dependencies via messaging wrapper
- **Domain Errors**: Business logic errors separate from infrastructure
- **Request Tracing**: End-to-end request tracking with correlation IDs
- **Multi-Tenancy**: Built-in merchant isolation and indexing

## Usage Examples

### Complete Service Setup
```python
from shared.api import setup_middleware
from shared.database import create_database_config, DatabaseSessionManager
from shared.messaging import JetStreamWrapper

# Database setup
db_config = create_database_config("YOUR_SERVICE_")
db_manager = DatabaseSessionManager(db_config.database_url)
await db_manager.init()

# Messaging setup  
messaging = JetStreamWrapper(logger)
await messaging.connect(["nats://localhost:4222"])
publisher = messaging.create_publisher(YourPublisher)

# Middleware setup
setup_middleware(app, service_name="your-service")
```

### Event Publishing
```python
# Publish with automatic correlation
await publisher.publish_event(
    subject="evt.item.created",
    payload={"item_id": str(item.id)},
    correlation_id=get_correlation_context(),
    idempotency_key=generate_idempotency_key("INTERNAL", "ITEM_CREATED", item.id)
)
```

### Error Handling
```python
from shared.errors import NotFoundError, ValidationError

# Use specific error types
if not item:
    raise NotFoundError(
        f"Item {item_id} not found",
        resource="item",
        resource_id=str(item_id)
    )
```

## Dependencies

- **FastAPI** - Web framework integration
- **SQLAlchemy** - Async database ORM
- **Pydantic** - Data validation and serialization
- **NATS.py** - JetStream messaging
- **Prometheus Client** - Metrics collection
- **Alembic** - Database migrations
- **PyYAML** - Configuration management

## License

Copyright © 2025 GlamYouUp. All rights reserved.