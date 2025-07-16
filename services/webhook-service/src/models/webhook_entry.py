# services/webhook-service/src/models/webhook_entry.py
"""Webhook entry database model."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Integer, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base, TimestampedMixin


class WebhookStatus(enum.Enum):
    """Webhook processing status"""
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class WebhookEntry(Base, TimestampedMixin):
    """
    Webhook entry model for storing webhook data and processing status.
    """
    
    __tablename__ = "webhook_entries"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    headers: Mapped[Dict[str, str]] = mapped_column(JSON, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[WebhookStatus] = mapped_column(
        SQLEnum(WebhookStatus), 
        nullable=False, 
        default=WebhookStatus.RECEIVED,
        index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<WebhookEntry(id={self.id}, platform={self.platform}, topic={self.topic}, status={self.status.value})>"

