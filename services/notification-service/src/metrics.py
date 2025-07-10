# -------------------------------
# services/notification-service/src/metrics.py
# -------------------------------

"""
Notification service specific metrics.

This module defines domain-specific metrics for the notification service
that extend the standard HTTP metrics from shared.
"""

from prometheus_client import Counter, Histogram, Gauge

# Notification-specific metrics
notifications_sent_total = Counter(
    "notifications_sent_total",
    "Total notifications sent",
    ["type", "provider", "status"],
)

notifications_duration_seconds = Histogram(
    "notifications_duration_seconds",
    "Notification sending duration in seconds",
    ["type", "provider"],
)

email_queue_size = Gauge("email_queue_size", "Current size of email queue")

template_render_duration_seconds = Histogram(
    "template_render_duration_seconds",
    "Template rendering duration in seconds",
    ["template_type"],
)

rate_limit_hits_total = Counter(
    "rate_limit_hits_total", "Total rate limit hits", ["merchant_id", "limit_type"]
)


# Helper functions for easier metric updates
def increment_notification_sent(notification_type: str, provider: str, status: str):
    """Increment notification sent counter."""
    notifications_sent_total.labels(
        type=notification_type, provider=provider, status=status
    ).inc()


def observe_notification_duration(
    notification_type: str, provider: str, duration: float
):
    """Record notification sending duration."""
    notifications_duration_seconds.labels(
        type=notification_type, provider=provider
    ).observe(duration)


def set_email_queue_size(size: int):
    """Update email queue size gauge."""
    email_queue_size.set(size)


def observe_template_render_duration(template_type: str, duration: float):
    """Record template rendering duration."""
    template_render_duration_seconds.labels(template_type=template_type).observe(
        duration
    )


def increment_rate_limit_hit(merchant_id: str, limit_type: str):
    """Increment rate limit hit counter."""
    rate_limit_hits_total.labels(merchant_id=merchant_id, limit_type=limit_type).inc()
