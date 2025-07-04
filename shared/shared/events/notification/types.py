from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from datetime import datetime
from uuid import UUID


from ..base import EventWrapper

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
    shop_id: UUID
    shop_domain: str
    email: str
    dynamic_content: Dict[str, Any] = Field(default_factory=dict)

class SendEmailCommandPayload(BaseModel):
    """Payload for sending a single email"""
    notification_type: str
    recipient: Recipient

class SendEmailBulkCommandPayload(BaseModel):
    """Payload for sending bulk emails by notification type"""
    notification_type: str
    recipients: List[Recipient]
    
class SendEmailCommand(EventWrapper):
    """Command to send a single email"""
    subject: str = NotificationCommands.NOTIFICATION_SEND_EMAIL
    data: SendEmailCommandPayload
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
class SendEmailBulkCommand(EventWrapper):
    """Command to send bulk emails with same notification type"""
    subject: str = NotificationCommands.NOTIFICATION_SEND_BULK
    data: SendEmailBulkCommandPayload
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
class EmailSentEventPayload(BaseModel):
    """Payload for NOTIFICATION_EMAIL_SENT event"""
    notification_id: UUID
    shop_id: UUID
    notification_type: str
    provider: str
    provider_message_id: str
    sent_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

class EmailFailedEventPayload(BaseModel):
    """Payload for NOTIFICATION_EMAIL_FAILED event"""
    notification_id: UUID
    shop_id: UUID
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
    
class EmailSentEvent(EventWrapper):
    """Event emitted when an email is successfully sent"""
    subject: str = NotificationEvents.NOTIFICATION_EMAIL_SENT
    data: EmailSentEventPayload
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
class EmailDeliveryFailedEvent(EventWrapper):
    """Event emitted when email delivery fails"""
    subject: str = NotificationEvents.NOTIFICATION_EMAIL_FAILED
    data: EmailFailedEventPayload
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
class BulkSendCompletedEvent(EventWrapper):
    """Event emitted when a bulk email send operation completes"""
    subject: str = NotificationEvents.NOTIFICATION_BULK_SEND_COMPLETED
    data: BulkCompletedEventPayload
    metadata:  Optional[Dict[str, Any]] = Field(default_factory=dict)


