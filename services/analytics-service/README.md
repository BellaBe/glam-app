"""
# Analytics Service

The Analytics Service is the intelligence hub that analyzes usage patterns, generates insights, provides predictive analytics, and enables data-driven decision making for shop behavior and platform operations.

## Features

### Core Analytics
- **Real-time Usage Tracking**: Process events in real-time with <100ms latency
- **Daily Aggregations**: Comprehensive daily rollups of usage, orders, and engagement
- **Feature Analytics**: Detailed performance metrics for selfie, match, and sort features
- **Time-series Analysis**: Leverages TimescaleDB for efficient time-series operations

### Predictive Intelligence
- **Churn Risk Prediction**: ML-powered churn risk assessment with confidence scores
- **Credit Depletion Forecasting**: Predict when merchants will exhaust credits
- **Trial Conversion Probability**: Analyze trial engagement to predict conversions
- **Growth Forecasting**: Revenue and usage growth predictions

### Pattern Detection
- **Usage Patterns**: Detect daily, weekly, seasonal, and behavioral patterns
- **Anomaly Detection**: Statistical anomaly detection for usage spikes and drops
- **Engagement Analysis**: Comprehensive user engagement scoring and trends

### Intelligent Alerting
- **Configurable Rules**: Flexible alert rules with multiple threshold operators
- **Multi-channel Notifications**: Email, webhook, and dashboard notifications
- **Smart Cooldowns**: Prevent alert spam with intelligent cooldown periods
- **Alert Templates**: Pre-configured templates for common scenarios

### Platform Analytics
- **Cohort Analysis**: Track merchant segments over time
- **Business Intelligence**: Revenue, MRR, ARR tracking and forecasting
- **Performance Monitoring**: Platform uptime, response times, and error rates

## Architecture

### Technology Stack
- **Framework**: FastAPI with async processing
- **Database**: PostgreSQL with TimescaleDB extension for time-series data
- **Cache**: Redis for computed metrics and real-time counters
- **Message Bus**: NATS JetStream for event streaming
- **ML Framework**: scikit-learn for predictive models

### Ports
- **Internal Port**: 8017 (container)
- **External Port**: 8117 (local development)
- **Metrics Port**: 9090

## Quick Start

### Development Setup

```bash
# From services/analytics-service/
make setup-dev
```

This will:
- Install dependencies with Poetry
- Set up pre-commit hooks
- Run database migrations
- Generate sample data for development

### Manual Setup

```bash
# Install dependencies
poetry install

# Set up configuration
cp .env.example ../../.env
# Edit .env with your database credentials

# Run migrations
poetry run alembic upgrade head

# Start the service
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8117 --reload
```

### Docker Setup

```bash
# Start all services
make docker-run

# View logs
make docker-logs

# Stop services
make docker-stop
```

## Configuration

The service uses a three-tier configuration system:

1. **Shared Configuration** (`config/shared.yml`)
2. **Service Configuration** (`config/services/analytics-service.yml`)
3. **Environment Variables** (`.env`)

### Key Configuration Options

```yaml
