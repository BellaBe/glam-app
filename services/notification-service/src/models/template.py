# File: services/notification-service/src/models/template.py

"""Notification template models."""

import enum
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, UniqueConstraint, Index, func, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, TimestampedMixin


class ChangeType(str,enum.Enum):
    """Type of template change."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"


class NotificationTemplate(Base, TimestampedMixin):
    """
    Email templates with variable placeholders.
    
    Stores reusable templates for different notification types
    with Jinja2-style variable substitution.
    """
    __tablename__ = "notification_templates"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    
    # Template identification
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Template content
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Template variables
    variables: Mapped[Dict[str, List[str]]] = mapped_column(
        JSONB,
        nullable=False,
        default={"required": [], "optional": []},
        comment="JSON object with 'required' and 'optional' arrays of variable names"
    )
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    history: Mapped[List["NotificationTemplateHistory"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<NotificationTemplate(name={self.name}, type={self.type})>"


class NotificationTemplateHistory(Base):
    """
    Audit trail for template changes.
    
    Tracks all modifications to notification templates for
    compliance and debugging purposes.
    """
    __tablename__ = "notification_template_history"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    
    # Template reference
    template_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notification_templates.id"),
        nullable=False,
        index=True
    )
    
    # Version tracking
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Historical data (snapshot at time of change)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Dict[str, List[str]]] = mapped_column(JSONB, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Change metadata
    changed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    change_type: Mapped[ChangeType] = mapped_column(Enum(ChangeType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )
    
    # Relationships
    template: Mapped["NotificationTemplate"] = relationship(back_populates="history")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('template_id', 'version', name='uq_template_version'),
        Index('idx_template_history_version', 'template_id', 'version'),
    )
    
    def __repr__(self):
        return f"<TemplateHistory(template_id={self.template_id}, version={self.version})>"