# services/notification-service/src/models/api.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from enum import Enum


class NotificationType(str, Enum):
    """Notification types"""
    # Shop notifications
    WELCOME = "welcome"
    REGISTRATION_FINISH = "registration_finish"
    REGISTRATION_SYNC = "registration_sync"
    BILLING_EXPIRED = "billing_expired"
    BILLING_CHANGED = "billing_changed"
    BILLING_LOW_CREDITS = "billing_low_credits"
    BILLING_ZERO_BALANCE = "billing_zero_balance"
    BILLING_DEACTIVATED = "billing_deactivated"
    # System notifications
    PASSWORD_RESET = "password_reset"
    ACCOUNT_VERIFIED = "account_verified"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class NotificationChannel(str, Enum):
    """Notification channels"""
    EMAIL = "email"
    # Future: SMS = "sms"
    # Future: PUSH = "push"


# Request Models
class SendEmailRequest(BaseModel):
    """Send email notification request"""
    shop_id: UUID
    shop_domain: str
    type: NotificationType
    to_email: EmailStr
    subject: Optional[str] = None
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BulkEmailRequest(BaseModel):
    """Bulk email notification request"""
    type: NotificationType
    recipients: List[Dict[str, Any]]  # [{shop_id, shop_domain, email, variables}]
    subject: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationPreferencesUpdate(BaseModel):
    """Update notification preferences"""
    email_enabled: Optional[bool] = None
    notification_types: Optional[Dict[NotificationType, bool]] = None
    timezone: Optional[str] = None


# Response Models
class NotificationResponse(BaseModel):
    """Notification response"""
    id: UUID
    shop_id: UUID
    shop_domain: str
    type: NotificationType
    channel: NotificationChannel
    subject: str
    status: NotificationStatus
    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationListResponse(BaseModel):
    """Paginated notification list"""
    data: List[NotificationResponse]
    meta: Dict[str, Any]


class NotificationTemplate(BaseModel):
    """Notification template"""
    id: UUID
    name: str
    type: NotificationType
    subject_template: str
    body_template: str
    variables: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NotificationTemplateCreate(BaseModel):
    """Create notification template"""
    name: str
    type: NotificationType
    subject_template: str
    body_template: str
    variables: List[str] = Field(default_factory=list)
    is_active: bool = True


class NotificationTemplateUpdate(BaseModel):
    """Update notification template"""
    name: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class NotificationPreferences(BaseModel):
    """Shop notification preferences"""
    shop_id: UUID
    shop_domain: str
    email_enabled: bool = True
    notification_types: Dict[NotificationType, bool] = Field(
        default_factory=lambda: {t: True for t in NotificationType}
    )
    timezone: str = "UTC"
    unsubscribe_token: str
    created_at: datetime
    updated_at: datetime


class EmailDeliveryResult(BaseModel):
    """Email delivery result"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class TemplatePreview(BaseModel):
    """Template preview result"""
    subject: str
    body_html: str
    body_text: Optional[str] = None
    variables_used: List[str]
    missing_variables: List[str] = Field(default_factory=list)