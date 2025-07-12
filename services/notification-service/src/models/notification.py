# File: services/notification-service/src/models/notification.py

"""Notification model and related enums."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import String, Text, Integer, DateTime, Enum, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from shared.database.base import MerchantMixin, Base, TimestampedMixin


class NotificationStatus(str, enum.Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"


class NotificationProvider(str, enum.Enum):
    """Email service providers."""
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    AWS_SES = "aws_ses"
    SMTP = "smtp"


class Notification(Base, TimestampedMixin, MerchantMixin):
    """
    Primary table for tracking all email notifications.
    
    Stores all sent and pending notifications with their status,
    content, and delivery information.
    """
    __tablename__ = "notifications"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Recipient and type
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Template reference (optional)
    template_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Email content
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Delivery status
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True
    )
    
    # Provider information
    provider: Mapped[Optional[NotificationProvider]] = mapped_column(
        Enum(NotificationProvider),
        nullable=True
    )
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_notifications_created_at', 'created_at'),
        Index('idx_notifications_merchant_status', 'merchant_id', 'status'),
        Index('idx_notifications_email_type', 'recipient_email', 'type'),
    )
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, status={self.status})>"