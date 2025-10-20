from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import TIMESTAMP, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .session import Base


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    merchant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    platform_name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_shop_id: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(100), nullable=False)
    template_variables: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default=NotificationStatus.PENDING)

    # Attempt tracking
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_attempt_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), default=None)
    last_attempt_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), default=None)
    delivered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), default=None)

    # Provider tracking
    provider_message_id: Mapped[str | None] = mapped_column(String(255), default=None)
    provider_message: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Idempotency
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    __table_args__ = (
        Index("notifications_merchant_id_first_attempt_at_idx", "merchant_id", "first_attempt_at"),
        Index("notifications_status_last_attempt_at_idx", "status", "last_attempt_at"),
        Index("notifications_provider_message_id_idx", "provider_message_id"),
        Index("notifications_idempotency_key_idx", "idempotency_key"),
    )
