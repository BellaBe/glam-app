# shared/events/notification/types.py
from pydantic import BaseModel, Field
from typing import Dict, List, Any
from datetime import datetime
from uuid import UUID

from shared.events.base import EventWrapper
from shared.events.context import EventContext


class NotificationCommands:
    """Notification command types"""

    NOTIFICATION_SEND_EMAIL = "cmd.notification.send_email"
    NOTIFICATION_SEND_BULK = "cmd.notification.bulk_send"


class NotificationEvents:
    """Notification event types"""

    NOTIFICATION_EMAIL_SENT = "evt.notification.email.sent"
    NOTIFICATION_EMAIL_FAILED = "evt.notification.email.failed"
    NOTIFICATION_BULK_SEND_COMPLETED = "evt.notification.bulk_send.completed"


class Recipient(BaseModel):
    merchant_id: UUID
    shop_domain: str
    email: str
    unsubscribe_token: str
    dynamic_content: Dict[str, Any] = Field(default_factory=dict)


class SendEmailCommandPayload(BaseModel):
    """Payload for sending a single email"""

    notification_type: str
    recipient: Recipient


class SendEmailBulkCommandPayload(BaseModel):
    """Payload for sending bulk emails by notification type"""

    notification_type: str
    recipients: List[Recipient]


# Event payloads
class EmailSentEventPayload(BaseModel):
    """Payload for NOTIFICATION_EMAIL_SENT event"""

    notification_id: UUID
    merchant_id: UUID
    notification_type: str
    provider: str
    provider_message_id: str
    sent_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}


class EmailFailedEventPayload(BaseModel):
    """Payload for NOTIFICATION_EMAIL_FAILED event"""

    notification_id: UUID
    merchant_id: UUID
    notification_type: str
    error: str
    error_code: str
    retry_count: int
    will_retry: bool
    failed_at: datetime


class BulkCompletedEventPayload(BaseModel):
    """Payload for bulk send completion"""

    bulk_job_id: UUID
    notification_type: str
    total_recipients: int
    total_sent: int
    total_failed: int
    total_skipped: int
    duration_seconds: float
    completed_at: datetime


# Now use the generic EventWrapper with specific payload types
class SendEmailCommand(EventWrapper[SendEmailCommandPayload]):
    """Command to send a single email"""

    subject: str = NotificationCommands.NOTIFICATION_SEND_EMAIL

    @classmethod
    def create_from_context(
        cls, context: EventContext, notification_type: str, recipient: Recipient
    ) -> "SendEmailCommand":
        """Create command with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=SendEmailCommandPayload(
                notification_type=notification_type, recipient=recipient
            ),
        )


class SendEmailBulkCommand(EventWrapper[SendEmailBulkCommandPayload]):
    """Command to send bulk emails with same notification type"""

    subject: str = NotificationCommands.NOTIFICATION_SEND_BULK

    @classmethod
    def create_from_context(
        cls, context: EventContext, notification_type: str, recipients: List[Recipient]
    ) -> "SendEmailBulkCommand":
        """Create bulk command with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=SendEmailBulkCommandPayload(
                notification_type=notification_type, recipients=recipients
            ),
        )


class EmailSentEvent(EventWrapper[EmailSentEventPayload]):
    """Event emitted when an email is successfully sent"""

    subject: str = NotificationEvents.NOTIFICATION_EMAIL_SENT

    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: EmailSentEventPayload
    ) -> "EmailSentEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=payload,
        )


class EmailDeliveryFailedEvent(EventWrapper[EmailFailedEventPayload]):
    """Event emitted when email delivery fails"""

    subject: str = NotificationEvents.NOTIFICATION_EMAIL_FAILED

    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: EmailFailedEventPayload
    ) -> "EmailDeliveryFailedEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=payload,
        )


class BulkSendCompletedEvent(EventWrapper[BulkCompletedEventPayload]):
    """Event emitted when a bulk email send operation completes"""

    subject: str = NotificationEvents.NOTIFICATION_BULK_SEND_COMPLETED

    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: BulkCompletedEventPayload
    ) -> "BulkSendCompletedEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=payload,
        )
