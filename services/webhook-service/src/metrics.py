# services/webhook-service/src/metrics.py
"""Metrics for webhook service."""

from prometheus_client import Counter, Histogram, Gauge
from shared.metrics import get_metrics_registry

# Get the shared metrics registry
registry = get_metrics_registry()

# Webhook processing metrics
webhooks_received_total = Counter(
    'webhooks_received_total',
    'Total number of webhooks received',
    ['platform', 'topic', 'status'],
    registry=registry
)

webhook_validation_failures_total = Counter(
    'webhook_validation_failures_total',
    'Total number of webhook validation failures',
    ['platform', 'reason'],
    registry=registry
)

webhook_processing_duration_seconds = Histogram(
    'webhook_processing_duration_seconds',
    'Time spent processing webhooks',
    ['platform', 'topic'],
    registry=registry
)

webhook_duplicate_total = Counter(
    'webhook_duplicate_total',
    'Total number of duplicate webhooks detected',
    ['platform'],
    registry=registry
)

# Current webhook status counts
webhooks_by_status = Gauge(
    'webhooks_by_status',
    'Current number of webhooks by status',
    ['platform', 'status'],
    registry=registry
)

# Platform handler metrics
platform_handlers_active = Gauge(
    'platform_handlers_active',
    'Number of active platform handlers',
    ['platform'],
    registry=registry
)