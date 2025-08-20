# services/notification-service/src/schemas/notification.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Output DTOs
class NotificationOut(BaseModel):
    """DTO for notification response"""

    id: UUID
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    shop_domain: str
    recipient_email: str
    template_type: str
    subject: str
    status: str
    provider: str | None = None
    provider_message_id: str | None = None
    error_message: str | None = None
    retry_count: int
    trigger_event: str
    trigger_event_id: str | None = None
    created_at: datetime
    sent_at: datetime | None = None
    failed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationStats(BaseModel):
    """DTO for notification statistics"""

    sent_today: int = 0
    failed_today: int = 0
    pending_today: int = 0
    by_template: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
