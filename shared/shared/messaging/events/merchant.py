from shared.messaging.events.base import BaseEventPayload


class MerchantCreatedPayload(BaseEventPayload):
    """Payload for merchant.created.v1 event."""

    shop_name: str
    email: str
    country: str
    currency: str
    timezone: str
    platform_version: str
    scopes: str
    status: str


class MerchantStatusChangedPayload(BaseEventPayload):
    """Payload for merchant.status.changed.v1 event."""

    old_status: str
    new_status: str
