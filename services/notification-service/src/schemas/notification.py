# services/notification-service/src/schemas/notification.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .enums import AttemptStatus, NotificationStatus


# Output DTOs
class NotificationOut(BaseModel):
    """DTO for notification response"""

    id: UUID
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    recipient_email: str
    template_type: str
    status: NotificationStatus
    provider_message_id: str | None = None
    trigger_event: str
    idempotency_key: str
    template_variables: dict  # JSON field
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationAttemptOut(BaseModel):
    """DTO for notification attempt"""

    id: UUID
    notification_id: UUID
    attempt_number: int
    provider: str
    status: AttemptStatus
    error_message: str | None = None
    provider_response: dict | None = None
    attempted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationWithAttemptsOut(BaseModel):
    """DTO for notification with attempts"""

    notification: NotificationOut
    attempts: list[NotificationAttemptOut] = Field(default_factory=list)


class NotificationStats(BaseModel):
    """DTO for notification statistics"""

    sent_today: int = 0
    failed_today: int = 0
    pending_today: int = 0
    by_template: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
