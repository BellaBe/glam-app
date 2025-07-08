# services/webhook-service/src/metrics.py
"""
Prometheus metrics for webhook service.

Tracks:
- Webhook reception and processing
- Platform-specific metrics
- Error rates
- Processing times
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# Service info
service_info = Info(
    "webhook_service",
    "Webhook service information"
)

# Webhook metrics
webhooks_received_total = Counter(
    "webhooks_received_total",
    "Total number of webhooks received",
    ["platform", "topic", "status"]
)

webhook_validation_failures_total = Counter(
    "webhook_validation_failures_total",
    "Total number of webhook validation failures",
    ["platform", "reason"]
)

webhook_processing_duration_seconds = Histogram(
    "webhook_processing_duration_seconds",
    "Time spent processing webhooks",
    ["platform", "topic"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

webhook_duplicate_total = Counter(
    "webhook_duplicate_total",
    "Total number of duplicate webhooks",
    ["platform"]
)

# Event publishing metrics
events_published_total = Counter(
    "webhook_events_published_total",
    "Total number of events published from webhooks",
    ["event_type", "platform"]
)

event_publishing_errors_total = Counter(
    "webhook_event_publishing_errors_total",
    "Total number of event publishing errors",
    ["event_type", "platform", "error_type"]
)

# Queue metrics
webhook_queue_size = Gauge(
    "webhook_queue_size",
    "Current size of webhook processing queue",
    ["platform"]
)

webhook_retry_queue_size = Gauge(
    "webhook_retry_queue_size",
    "Current size of webhook retry queue"
)

# Platform-specific metrics
shopify_webhooks_total = Counter(
    "shopify_webhooks_total",
    "Total Shopify webhooks by topic",
    ["topic", "shop_id"]
)

# Helper functions

def record_webhook_received(platform: str, topic: str, status: str = "success"):
    """Record webhook received"""
    webhooks_received_total.labels(
        platform=platform,
        topic=topic,
        status=status
    ).inc()


def record_webhook_validation_failure(platform: str, reason: str):
    """Record webhook validation failure"""
    webhook_validation_failures_total.labels(
        platform=platform,
        reason=reason
    ).inc()


def observe_webhook_processing_time(platform: str, topic: str, duration: float):
    """Observe webhook processing duration"""
    webhook_processing_duration_seconds.labels(
        platform=platform,
        topic=topic
    ).observe(duration)


def record_duplicate_webhook(platform: str):
    """Record duplicate webhook"""
    webhook_duplicate_total.labels(platform=platform).inc()


def record_event_published(event_type: str, platform: str):
    """Record event published"""
    events_published_total.labels(
        event_type=event_type,
        platform=platform
    ).inc()


def record_event_publishing_error(event_type: str, platform: str, error_type: str):
    """Record event publishing error"""
    event_publishing_errors_total.labels(
        event_type=event_type,
        platform=platform,
        error_type=error_type
    ).inc()


# Initialize service info
def init_metrics(service_name: str, version: str, environment: str):
    """Initialize service metrics"""
    service_info.info({
        "service": service_name,
        "version": version,
        "environment": environment
    })