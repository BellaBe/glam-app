# services/billing-service/src/events/types.py
class BillingEvents:
    """Event type constants for billing service"""
    
    # Subscription events
    SUBSCRIPTION_CREATED = "evt.billing.subscription.created"
    SUBSCRIPTION_ACTIVATED = "evt.billing.subscription.activated"
    SUBSCRIPTION_CANCELLED = "evt.billing.subscription.cancelled"
    SUBSCRIPTION_EXPIRED = "evt.billing.subscription.expired"
    
    # Purchase events
    PURCHASE_CREATED = "evt.billing.purchase.created"
    PURCHASE_COMPLETED = "evt.billing.purchase.completed"
    PURCHASE_FAILED = "evt.billing.purchase.failed"
    
    # Trial events
    TRIAL_EXTENDED = "evt.billing.trial.extended"
    TRIAL_EXPIRED = "evt.billing.trial.expired"
    
    # Notification events
    NOTIFICATION_PAYMENT_FAILED = "evt.billing.notification.payment_failed"
    NOTIFICATION_SUBSCRIPTION_ACTIVATED = "evt.billing.notification.subscription_activated"

