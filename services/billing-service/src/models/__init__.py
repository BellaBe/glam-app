# services/billing-service/src/models/__init__.py
"""Database models for billing service."""
from shared.database.base import Base, TimestampedMixin
from shared.database.base import MerchantMixin
from .billing_plan import BillingPlan, BillingInterval
from .one_time_purchase import OneTimePurchase, PurchaseStatus
from .subscription import Subscription, SubscriptionStatus
from .trial_extension import TrialExtension, TrialExtensionReason


__all__ = [
    # Base (from shared)
    "Base",
    "TimestampedMixin",
    # Local mixins
    "MerchantMixin",
    # One-time purchase
    "OneTimePurchase",
    "PurchaseStatus",
    # Subscription
    "Subscription",
    "SubscriptionStatus",
    # Trial extension
    "TrialExtension",
    "TrialExtensionReason",
    # Billing Plan
    "BillingPlan",
    "BillingInterval",
]


