# Scheduler Service

Generic job scheduling service for the GlamYouUp platform. Manages time-based and event-driven task execution with support for recurring schedules, one-time executions, and complex scheduling patterns.

## Features

- **Multiple Schedule Types**
  - Cron expressions for complex recurring patterns
  - Fixed intervals
  - One-time scheduled executions
  - Immediate execution
  
- **Robust Execution**
  - Distributed locking to prevent duplicate executions
  - Automatic retry with exponential backoff
  - Misfire handling
  - Execution history tracking
  
- **Flexible Command Routing**
  - Send commands to any service via NATS
  - Dynamic payload configuration
  - Command whitelisting for security
  
- **Management Features**
  - Pause/resume schedules
  - Bulk operations
  - Tag-based organization
  - Creator-based rate limiting

## Architecture

### Service Type
- **Type**: Worker Service with API endpoints
- **Port**: 8008
- **Database**: PostgreSQL (dedicated)
- **Dependencies**: Redis (for locks), APScheduler

### Key Components

1. **APScheduler Integration**
   - Persistent job store in PostgreSQL
   - AsyncIO executor for non-blocking execution
   - Automatic job recovery on restart

2. **Distributed Locking**
   - Redis-based locks
   - Prevents duplicate executions across instances
   - Configurable timeout and retry

3. **Event-Driven Architecture**
   - Subscribes to scheduling commands
   - Publishes execution events
   - Full async/await support

## API Endpoints

### Schedule Management
- `POST /api/v1/schedules` - Create schedule
- `GET /api/v1/schedules` - List schedules
- `GET /api/v1/schedules/{id}` - Get schedule details
- `PUT /api/v1/schedules/{id}` - Update schedule
- `DELETE /api/v1/schedules/{id}` - Delete schedule
- `POST /api/v1/schedules/{id}/pause` - Pause schedule
- `POST /api/v1/schedules/{id}/resume` - Resume schedule
- `POST /api/v1/schedules/{id}/trigger` - Trigger immediate execution

### Bulk Operations
- `POST /api/v1/schedules/bulk/create` - Create multiple schedules
- `POST /api/v1/schedules/bulk/operation` - Bulk pause/resume/delete

### Execution History
- `GET /api/v1/executions` - List all executions
- `GET /api/v1/executions/{id}` - Get execution details
- `GET /api/v1/executions/running` - Get running executions
- `GET /api/v1/schedules/{id}/executions` - Get schedule's executions
- `GET /api/v1/executions/stats/{schedule_id}` - Get execution statistics

### Health
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with dependencies
- `GET /ready` - Kubernetes readiness probe
- `GET /live` - Kubernetes liveness probe

## Configuration

### Environment Variables

```env
# Service Configuration
SERVICE_NAME=scheduler-service
SERVICE_VERSION=1.0.0
API_PORT=8008

# Scheduler Configuration
SCHEDULER_TIMEZONE=UTC
SCHEDULER_MISFIRE_GRACE_TIME=300
SCHEDULER_MAX_INSTANCES=3
SCHEDULER_EXECUTOR_POOL_SIZE=10

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
LOCK_TIMEOUT_SECONDS=300

# Operational
MAX_SCHEDULE_LOOKAHEAD_DAYS=365
DEFAULT_MAX_RETRIES=3
DEFAULT_RETRY_DELAY=300
MAX_SCHEDULES_PER_CREATOR=1000
```

## Usage Examples

### Create a Daily Email Schedule
```bash
curl -X POST http://localhost:8008/api/v1/schedules \
  -H "Content-Type: application/json" \
  -H "X-Created-By: notification-service" \
  -d '{
    "name": "daily_summary_emails",
    "description": "Send daily summary emails at 9 AM",
    "schedule_type": "cron",
    "cron_expression": "0 9 * * *",
    "timezone": "America/New_York",
    "target_command": "cmd.notification.send.bulk",
    "command_payload": {
      "notification_type": "daily_summary",
      "recipient_filter": "active_users"
    },
    "tags": ["email", "daily", "summary"],
    "priority": 7
  }'
```

### Create an Interval Schedule
```bash
curl -X POST http://localhost:8008/api/v1/schedules \
  -H "Content-Type: application/json" \
  -H "X-Created-By: analytics-service" \
  -d '{
    "name": "hourly_metrics_collection",
    "schedule_type": "interval",
    "interval_seconds": 3600,
    "target_command": "cmd.analytics.collect.metrics",
    "command_payload": {
      "metrics": ["sales", "traffic", "conversions"]
    },
    "max_retries": 5
  }'
```

### Trigger Immediate Execution
```bash
curl -X POST http://localhost:8008/api/v1/schedules/{schedule_id}/trigger \
  -H "X-Triggered-By: admin"
```

### Bulk Pause Schedules
```bash
curl -X POST http://localhost:8008/api/v1/schedules/bulk/operation \
  -H "Content-Type: application/json" \
  -H "X-Performed-By: admin" \
  -d '{
    "schedule_ids": ["uuid1", "uuid2", "uuid3"],
    "operation": "pause",
    "reason": "Maintenance window"
  }'
```

## Development

### Setup
```bash
# Install dependencies
poetry install

# Run migrations
alembic upgrade head

# Start service
poetry run uvicorn src.main:app --reload --port 8008
```

### Testing
```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=src
```

### Docker
```bash
# Build and run with docker-compose
docker-compose up --build

# Run only the service (requires external dependencies)
docker build -t scheduler-service .
docker run -p 8008:8008 scheduler-service
```

## Monitoring

### Metrics (Prometheus)
- `schedules_total{type,status}` - Total schedules by type and status
- `schedule_executions_total{schedule_type,status}` - Execution counter
- `schedule_execution_duration_seconds` - Execution time histogram
- `schedule_misfires_total` - Missed executions
- `distributed_locks_acquired_total` - Lock acquisition counter

### Logging
Structured JSON logging with correlation IDs for request tracing.

### Alerts
- High misfire rate (>5%)
- Execution failures (>10% in 5 min)
- Lock acquisition timeouts
- Long-running executions

## Error Handling

- **Transient Failures**: Automatic retry with exponential backoff
- **Lock Conflicts**: Skip execution, log as misfire
- **Invalid Schedules**: Disable and alert
- **Command Failures**: Configurable retry policy

## Security

- Command whitelisting
- Payload validation
- Creator-based rate limiting
- Audit trail for all modifications

## Future Enhancements

- Schedule templates
- Dynamic payload generation
- Webhook support
- Schedule dependencies
- Advanced retry strategies