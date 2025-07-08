# services/webhook-service/src/models/webhook_entry.py
"""Webhook entry model for storing all received webhooks."""

from enum import Enum
from uuid import UUID, uuid4
from sqlalchemy import String, Text, JSON, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from shared.database.base import TimestampedMixin
from .base import Base, ShopMixin


class WebhookSource(str, Enum):
    """Supported webhook sources"""
    SHOPIFY = "SHOPIFY"
    STRIPE = "STRIPE"
    OTHER = "OTHER"


class WebhookStatus(str, Enum):
    """Webhook processing status"""
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class WebhookEntry(Base, TimestampedMixin, ShopMixin):
    """Store all webhook entries for audit and replay"""
    
    __tablename__ = "webhook_entries"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    # Source and topic
    source: Mapped[WebhookSource] = mapped_column(
        SQLEnum(WebhookSource), 
        nullable=False,
        index=True
    )
    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Request data
    headers: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    hmac_signature: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Processing status
    status: Mapped[WebhookStatus] = mapped_column(
        SQLEnum(WebhookStatus),
        nullable=False,
        default=WebhookStatus.RECEIVED,
        index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Idempotency
    idempotency_key: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        unique=True,
        index=True
    )
    
    # Audit
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )