# services/credit-service/src/metrics.py
"""Metrics for credit service."""

from src.schemas.plugin_status import PluginStatus

from prometheus_client import Counter, Histogram, Gauge

# Transaction metrics
transaction_created_total = Counter(
    "credits_transactions_total",
    "Total credit transactions created",
    ["type", "reference_type"],
)

balance_updated_total = Counter(
    "credits_balance_updated_total", "Total balance updates"
)

# Processing time
transaction_processing_seconds = Histogram(
    "credits_transaction_processing_seconds",
    "Time spent processing credit transactions",
)

# Balance metrics
merchant_balance_total = Gauge(
    "credits_balance_total", "Current credit balance per merchant", ["merchant_id"]
)

merchants_zero_balance = Gauge(
    "credits_merchants_zero_balance", "Number of merchants with zero balance"
)

merchants_low_balance = Gauge(
    "credits_merchants_low_balance", "Number of merchants with low balance"
)

# Plugin status metrics
plugin_status_checks_total = Counter(
    "credits_plugin_status_checks_total", "Total plugin status checks", ["status"]
)

plugin_status_distribution = Gauge(
    "credits_plugin_status", "Plugin status distribution", ["status"]
)

# Event metrics
events_published_total = Counter(
    "credits_events_published_total", "Total events published", ["subject"]
)


# Helper functions
def increment_transaction_created(
    transaction_type: str, reference_type: str = "unknown"
):
    """Increment transaction created counter"""
    transaction_created_total.labels(
        type=transaction_type, reference_type=reference_type
    ).inc()


def increment_balance_updated():
    """Increment balance updated counter"""
    balance_updated_total.inc()


def observe_transaction_processing_time(duration_seconds: float):
    """Record transaction processing time"""
    transaction_processing_seconds.observe(duration_seconds)


def set_merchant_balance_gauge(merchant_id: str, balance: float):
    """Set merchant balance gauge"""
    merchant_balance_total.labels(merchant_id=merchant_id).set(balance)


def increment_plugin_status_check(status: PluginStatus):
    """Increment plugin status check counter"""
    plugin_status_checks_total.labels(status=status).inc()


def set_plugin_status_distribution(status: str, count: int):
    """Set plugin status distribution"""
    plugin_status_distribution.labels(status=status).set(count)


def increment_event_published(subject: str):
    """Increment events published counter"""
    events_published_total.labels(subject=subject).inc()
