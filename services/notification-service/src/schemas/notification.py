# File: services/notification-service/src/schemas/notification.py

"""Notification-related request and response schemas."""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict, conlist
from uuid import UUID

from ..models.notification import NotificationStatus, NotificationProvider
from .common import ShopInfo, DateRangeFilter, SortOrder


# Request Schemas

class NotificationCreate(ShopInfo):
    """Create a new notification request."""
    notification_type: str = Field(..., min_length=1, max_length=50)
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("shop_id", "shop_domain", "shop_email", "unsubscribe_token")
    def validate_content_source(cls, v):
        """Ensure required fields are provided."""
        if not v:
            raise ValueError("This field is required")
        return v

class BulkNotificationCreate(BaseModel):
    """Create multiple notifications at once."""
    notification_type: str = Field(..., min_length=1, max_length=50)
    recipients: List[ShopInfo] = Field(..., min_length=1, max_length=100)

    @field_validator('recipients')
    def validate_recipients(cls, v):
        """Validate recipients list size and required fields."""
        if not (1 <= len(v) <= 100):
            raise ValueError("Recipients list must have between 1 and 100 items")
        for recipient in v:
            if not recipient.shop_id or not recipient.shop_domain or not recipient.shop_email or not recipient.unsubscribe_token:
                raise ValueError("Each recipient must have shop_id, shop_domain, shop_email, and unsubscribe_token")
        return v

class NotificationUpdate(BaseModel):
    """Update notification status."""
    status: NotificationStatus
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None


class NotificationFilter(BaseModel):
    """Filter parameters for notification queries."""
    shop_id: Optional[UUID] = None
    recipient_email: Optional[EmailStr] = None
    type: Optional[str] = None
    status: Optional[NotificationStatus] = None
    provider: Optional[NotificationProvider] = None
    date_range: Optional[DateRangeFilter] = None
    sort_by: str = Field("created_at", pattern="^(created_at|sent_at|status|type)$")
    sort_order: SortOrder = SortOrder.DESC


# Response Schemas

class NotificationResponse(BaseModel):
    """Basic notification response."""
    id: UUID
    shop_id: UUID
    shop_domain: str
    shop_email: str
    type: str
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class NotificationDetailResponse(NotificationResponse):
    """Detailed notification response with full information."""
    content: str
    provider: Optional[NotificationProvider] = None
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    extra_metadata: Optional[Dict[str, Any]] = None


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""
    notifications: List[NotificationResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool
