# services/webhook-service/src/models/platform_configuration.py
"""Platform configuration database model."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Boolean, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base, TimestampedMixin


class PlatformConfiguration(Base, TimestampedMixin):
    """
    Platform configuration model for storing webhook platform settings.
    """
    
    __tablename__ = "platform_configurations"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    webhook_secret: Mapped[str] = mapped_column(Text, nullable=False)  # Should be encrypted
    api_version: Mapped[str] = mapped_column(String(20), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    endpoints: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    def __repr__(self) -> str:
        return f"<PlatformConfiguration(id={self.id}, platform={self.platform}, active={self.active})>"
