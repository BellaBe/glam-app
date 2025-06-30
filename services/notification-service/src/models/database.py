# services/notification-service/src/models/database.py
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, 
    UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from shared.database.base import Base, TimestampedMixin, SoftDeleteMixin


class NotificationType(str, PyEnum):
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


class NotificationStatus(str, PyEnum):
    """Notification status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class Notification(Base, TimestampedMixin):
    """Notification history"""
    __tablename__ = "notifications"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    shop_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    shop_domain = Column(String(255), nullable=False)
    type = Column(Enum(NotificationType), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True)
    provider_message_id = Column(String(255))
    sent_at = Column(DateTime)
    metadata = Column(JSON, default={})
    
    __table_args__ = (
        Index("idx_shop_type_created", "shop_id", "type", "created_at"),
    )


class NotificationTemplate(Base, TimestampedMixin):
    """Email templates"""
    __tablename__ = "notification_templates"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(Enum(NotificationType), nullable=False, unique=True)
    subject_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    variables = Column(JSON, default=[])
    is_active = Column(Boolean, nullable=False, default=True)


class NotificationPreferences(Base, TimestampedMixin):
    """Shop notification preferences"""
    __tablename__ = "notification_preferences"
    
    shop_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    shop_domain = Column(String(255), nullable=False)
    email_enabled = Column(Boolean, nullable=False, default=True)
    notification_types = Column(JSON, default={})  # {type: enabled}
    timezone = Column(String(50), nullable=False, default="UTC")
    unsubscribe_token = Column(String(255), nullable=False, unique=True)


class NotificationFrequencyLimit(Base, TimestampedMixin):
    """Track frequency limits for notifications"""
    __tablename__ = "notification_frequency_limits"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    shop_id = Column(PG_UUID(as_uuid=True), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    send_count = Column(Integer, nullable=False, default=0)
    first_sent_at = Column(DateTime)
    last_sent_at = Column(DateTime)
    reset_at = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint("shop_id", "notification_type", name="uq_shop_notification_type"),
        Index("idx_shop_type", "shop_id", "notification_type"),
    )