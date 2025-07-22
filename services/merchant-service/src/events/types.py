# services/merchant-service/src/events/types.py
class MerchantEvents:
    """Event type constants"""
    MERCHANT_CREATED = "evt.merchant.created"
    MERCHANT_ACTIVATED = "evt.merchant.activated"
    MERCHANT_SUSPENDED = "evt.merchant.suspended"
    MERCHANT_DEACTIVATED = "evt.merchant.deactivated"
    STATUS_CHANGED = "evt.merchant.status.changed"
    CONFIG_UPDATED = "evt.merchant.config.updated"
    ACTIVITY_RECORDED = "evt.merchant.activity.recorded"
    ONBOARDING_STARTED = "evt.merchant.onboarding.started"
    ONBOARDING_COMPLETED = "evt.merchant.onboarding.completed"