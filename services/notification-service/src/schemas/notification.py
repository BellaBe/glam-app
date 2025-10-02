# services/notification-service/src/schemas/notification.py

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationOut(BaseModel):
    """DTO for notification response"""

    id: UUID
    merchant_id: str  # String representation of UUID
    platform_name: str
    platform_shop_id: str
    domain: str
    recipient_email: str
    template_type: str
    template_variables: dict  # JSON field
    status: NotificationStatus | str  # Accept both enum and string
    attempt_count: int
    first_attempt_at: datetime | None
    last_attempt_at: datetime | None
    delivered_at: datetime | None = None
    provider_message_id: str | None = None
    provider_message: dict | None = None  # JSON field
    idempotency_key: str

    @field_validator("status", mode="before")
    def validate_status(cls, v):
        """Convert string to enum if necessary"""
        if isinstance(v, str):
            return NotificationStatus(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class NotificationStats(BaseModel):
    """DTO for notification statistics"""

    sent_today: int = 0
    failed_today: int = 0
    pending_today: int = 0
    by_template: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
