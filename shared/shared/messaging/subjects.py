# shared/shared/messaging/subjects.py
"""NATS subjects for microservices."""

from enum import Enum


class Subjects(str, Enum):
    """NATS subjects for the notification service"""

    # Notification events
    NOTIFICATION_EMAIL_REQUESTED = "cmd.notification.email.send.v1"
    NOTIFICATION_EMAIL_SENT = "evt.notification.email.sent.v1"
    NOTIFICATION_EMAIL_FAILED = "evt.notification.email.failed.v1"

    # Billing subjects
    BILLING_TRIAL_STARTED = "evt.billing.trial.started.v1"
    BILLING_TRIAL_EXPIRED = "evt.billing.trial.expired.v1"
    BILLING_CREDITS_PURCHASED = "evt.billing.credits.purchased.v1"

    # Merchant subjects
    MERCHANT_CREATED = "evt.merchant.created.v1"

    # Catalog subjects
    CATAlOG_SYNC_STARTED = "evt.catalog.sync.started.v1"
    CATALOG_SYNC_COMPLETED = "evt.catalog.sync.completed.v1"
    CATALOG_SYNC_FAILED = "evt.catalog.sync.failed.v1"

    # Credit events
    CREDIT_BALANCE_LOW = "evt.credit.balance.low.v1"
    CREDIT_BALANCE_DEPLETED = "evt.credit.balance.depleted.v1"
    CREDITS_CONSUMED = "evt.credits.consumed.v1"
    CREDITS_RESET = "evt.credits.reset.v1"

    # Analytics events
    ANALYTICS_EVENT_TRACKED = "evt.analytics.tracked.v1"
    ANALYTICS_AGGREGATED = "evt.analytics.aggregated.v1"

    # Webhook events
    WEBHOOK_RECEIVED = "evt.webhook.received.v1"
    WEBHOOK_PROCESSED = "evt.webhook.processed.v1"
    WEBHOOK_FAILED = "evt.webhook.failed.v1"
