# services/notification-service/src/schemas/events.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from shared.messaging.events.base import BaseEventPayload

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
