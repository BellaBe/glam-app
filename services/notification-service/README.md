# Notification Service

Email notification service for the GlamYouUp platform.

## Features

- Multiple email provider support (SendGrid, AWS SES, SMTP)
- Automatic failover between providers
- Template management with Jinja2
- Rate limiting per recipient and notification type
- Bulk email sending
- Notification preferences per shop
- Event-driven architecture with NATS JetStream
- Complete audit trail

## Architecture

### Service Type
- **Type**: API Service with Event Subscribers
- **Port**: 8007
- **Database**: PostgreSQL (dedicated)

### Key Components

1. **Email Providers**
   - SendGrid (primary)
   - AWS SES (fallback)
   - SMTP (additional fallback)

2. **Template Engine**
   - Jinja2 for template rendering
   - Variable validation
   - HTML to text conversion

3. **Rate Limiting**
   - Per-recipient limits
   - Per-notification-type limits
   - Burst protection

4. **Event Handling**
   - Subscribes to: `cmd.notification.send.email`, `cmd.notification.send.bulk`
   - Publishes: `evt.notification.email.sent`, `evt.notification.email.failed`

## API Endpoints

### Notifications
- `GET /api/v1/notifications` - List notifications with pagination
- `GET /api/v1/notifications/{id}` - Get notification details

### Templates
- `GET /api/v1/notifications/templates` - List templates
- `GET /api/v1/notifications/templates/{id}` - Get template
- `POST /api/v1/notifications/templates` - Create template
- `PUT /api/v1/notifications/templates/{id}` - Update template
- `DELETE /api/v1/notifications/templates/{id}` - Delete template
- `POST /api/v1/notifications/templates/{id}/preview` - Preview template
- `POST /api/v1/notifications/templates/{id}/validate` - Validate template
- `POST /api/v1/notifications/templates/{id}/clone` - Clone template

### Preferences
- `POST /api/v1/notifications/preferences` - Update preferences
- `GET /api/v1/notifications/preferences/{shop_id}` - Get preferences

## Environment Variables

See `.env.example` for all configuration options.

## Development

```bash
# Install dependencies
poetry install

# Run migrations
alembic upgrade head

# Start service
uvicorn app.main:app --reload --port 8007

# Run tests
pytest

Docker
bash# Build image
docker build -t notification-service .

# Run with docker-compose
docker-compose up notification-service
Database Migrations
bash# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
Template Variables
Global Variables (always available)

unsubscribe_url - Unsubscribe link
support_url - Support page link
current_year - Current year
platform_name - "GlamYouUp"

Template-Specific Variables
Defined per template in the variables field:

required: Must be provided
optional: Can be provided

Rate Limits
Default Limits

10 emails per minute per recipient
20 burst limit
1000 daily limit

Type-Specific Limits

billing_low_credits: Max 5 total
billing_zero_balance: Max 2 total
billing_deactivated: Max 7 total

