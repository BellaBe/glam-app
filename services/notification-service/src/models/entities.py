from sqlalchemy import String, Boolean, Text, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base, TimestampedMixin
from typing import Optional
import uuid
from datetime import datetime, timezone

class Notification(Base, TimestampedMixin):
    """Notification model"""
    __tablename__ = "notifications"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    shop_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    template_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

class NotificationTemplate(Base, TimestampedMixin):
    """Notification template model"""
    __tablename__ = "notification_templates"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

class NotificationTemplateHistory(Base):
    """Template history for audit trail"""
    __tablename__ = "notification_template_history"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

class NotificationPreference(Base, TimestampedMixin):
    """Shop notification preferences"""
    __tablename__ = "notification_preferences"
    
    shop_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shop_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_types: Mapped[dict] = mapped_column(JSON, default=dict)
    unsubscribe_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

class NotificationRateLimit(Base):
    """Rate limiting tracking"""
    __tablename__ = "notification_rate_limits"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    notification_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    send_count: Mapped[int] = mapped_column(Integer, default=0)
    window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    
class BatchJob(Base):
    """Model for tracking batch notification jobs"""
    __tablename__ = "batch_jobs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    template_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    recipient_count: Mapped[int] = mapped_column(Integer, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # pending, processing, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)