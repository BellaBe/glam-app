# services/notification-service/src/schemas/events.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from shared.messaging.events.base import BaseEventPayload


# Merchant events
class MerchantCreatedPayload(BaseEventPayload):
    """Payload for merchant.created event"""

    email: EmailStr
    shop_name: str
    installed_at: datetime


# Catalog events
class CatalogSyncCompletedPayload(BaseEventPayload):
    """Payload for catalog.sync.completed event"""

    sync_id: UUID
    total_items: int
    status: str
    first_sync: bool
    has_changes: bool
    added_count: int = 0
    updated_count: int = 0


class BillingFreeTrialStartedPayload(BaseEventPayload):
    """Payload for billing.free_trial.started event"""

    trial_id: UUID


# Billing events
class BillingSubscriptionExpiredPayload(BaseEventPayload):
    """Payload for billing.subscription.expired event"""

    plan_name: str
    expired_at: datetime


class BillingSubscriptionChangedPayload(BaseEventPayload):
    """Payload for billing.subscription.changed event"""

    old_plan: str | None
    new_plan: str
    changed_at: datetime


# Credit events
class CreditBalanceLowPayload(BaseEventPayload):
    """Payload for credit.balance.low event"""

    balance: int
    threshold: int


class CreditBalanceDepletedPayload(BaseEventPayload):
    """Payload for credit.balance.depleted event"""

    depleted_at: datetime


# Published events
class NotificationSentPayload(BaseEventPayload):
    """Payload for notification.email.sent event"""

    notification_id: UUID
    template_type: str
    delivered_at: datetime
    provider: str | None = None


class EmailFailedPayload(BaseModel):
    """Payload for notification.email.failed event"""

    notification_id: UUID
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    domain: str
    template_type: str
    error: str
    failed_at: datetime
