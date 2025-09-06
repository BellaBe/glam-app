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
    BILLING_TRIAL_ACTIVATED = "evt.billing.trial.activated.v1"
    BILLING_PURCHASE_COMPLETED = "evt.billing.purchase.completed.v1"

    # Merchant subjects
    MERCHANT_CREATED = "evt.merchant.created.v1"
    MERCHANT_STATUS_CHANGED = "evt.merchant.status.changed.v1"

    # Catalog subjects
    CATAlOG_SYNC_STARTED = "evt.catalog.sync.started.v1"
    CATALOG_SYNC_COMPLETED = "evt.catalog.sync.completed.v1"
    CATALOG_SYNC_FAILED = "evt.catalog.sync.failed.v1"

    # Credit events
    CREDIT_BALANCE_LOW = "evt.credit.balance.low.v1"
    CREDIT_BALANCE_DEPLETED = "evt.credit.balance.depleted.v1"
    CREDIT_TRIAL_EXHAUSTED = "evt.credit.trial.exhausted.v1"

    # Analytics events
    ANALYTICS_EVENT_TRACKED = "evt.analytics.tracked.v1"
    ANALYTICS_AGGREGATED = "evt.analytics.aggregated.v1"

    # Webhook events
    WEBHOOK_RECEIVED = "evt.webhook.received.v1"
    WEBHOOK_PROCESSED = "evt.webhook.processed.v1"
    WEBHOOK_FAILED = "evt.webhook.failed.v1"
