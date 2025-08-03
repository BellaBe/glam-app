# shared/events/payloads/notification.py

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from enum import Enum


class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    URGENT = "urgent"


class EmailSendRequested(BaseModel):
    """Payload for email send requested event"""
    merchant_id: UUID
    merchant_domain: str = Field(..., min_length=1, max_length=100)
    email_type: str = Field(..., min_length=1, max_length=100)
    recipient_email: EmailStr
    extra_metadata: Optional[Dict[str, Any]] = None

class EmailSendBulkRequested(BaseModel):
    """Payload for bulk email send requested event"""
    merchant_id: UUID
    email_type: str = Field(..., min_length=1, max_length=100)
    recipient_emails: list[EmailStr]
    template_context: Dict[str, Any] = Field(default_factory=dict)
    priority: EmailPriority = EmailPriority.NORMAL
    requested_by: str = Field(..., min_length=1)
    send_at: Optional[datetime] = None
    bulk_job_id: Optional[str] = None


class EmailSendComplete(BaseModel):
    """Payload for email sent event"""
    notification_id: UUID
    merchant_id: UUID
    email_type: str
    recipient_email: EmailStr
    provider: str
    provider_message_id: Optional[str] = None
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmailSendFailed(BaseModel):
    """Payload for email failed event"""
    notification_id: Optional[UUID] = None
    merchant_id: UUID
    template_name: str
    recipient_email: EmailStr
    error_message: str
    error_code: str
    retry_count: int = Field(default=0, ge=0)
    will_retry: bool = False
    
class EmailSendBulkComplete(BaseModel):
    """Payload for bulk email completion event"""
    merchant_id: UUID
    email_type: str
    total_sent: int
    total_failed: int
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[Dict[str, Any]] = None
    
class EmailSendBulkFailed(BaseModel):
    """Payload for bulk email failed event"""
    merchant_id: UUID
    email_type: str
    error_message: str
    error_code: str
    retry_count: int = Field(default=0, ge=0)
    will_retry: bool = False
    failed_recipients: Optional[list[EmailStr]] = None