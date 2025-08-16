# shared/shared/messaging/subjects.py
"""NATS subjects for microservices."""

from enum import Enum

class Subjects(str, Enum):
    """NATS subjects for the notification service"""
    EMAIL_SEND_REQUESTED = "cmd.email.send.requested.v1"
    EMAIL_SEND_COMPLETE = "evt.email.send.complete.v1"
    EMAIL_SEND_FAILED = "evt.email.send.failed.v1"
    EMAIL_SEND_BOUNCED = "evt.email.send.bounced.v1"
    EMAIL_SEND_BULK_REQUESTED = "cmd.email.send.bulk.requested.v1"
    EMAIL_SEND_BULK_STARTED = "evt.email.send.bulk.started.v1"
    EMAIL_SEND_BULK_COMPLETE = "evt.email.send.bulk.complete.v1"
    EMAIL_SEND_BULK_FAILED = "evt.email.send.bulk.failed.v1"
    
    # Billing subjects
    BILLING_TRIAL_STARTED = "evt.billing.trial.started.v1"
    BILLING_TRIAL_EXPIRED = "evt.billing.trial.expired.v1"
    BILLING_CREDITS_PURCHASED = "evt.billing.credits.purchased.v1"
    