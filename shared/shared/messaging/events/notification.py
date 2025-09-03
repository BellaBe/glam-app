# shared/shared/messaging/events/notification.py
from uuid import UUID

from shared.messaging.events.base import BaseEventPayload


class EmailSentPayload(BaseEventPayload):
    """Payload for email sent event"""

    notification_id: UUID
    template_type: str
    recipient_email: str
    provider: str
    provider_message_id: str


class EmailFailedPayload(BaseEventPayload):
    """Payload for email failed event"""

    notification_id: UUID
    template_type: str
    recipient_email: str
    error_code: str
    error_message: str
    retry_count: int = 0
