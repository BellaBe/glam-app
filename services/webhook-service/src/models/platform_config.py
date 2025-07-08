# services/webhook-service/src/models/platform_config.py
"""Platform configuration for webhook secrets and settings."""

from uuid import UUID, uuid4
from sqlalchemy import String, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from shared.database.base import TimestampedMixin
from .base import Base
from .webhook_entry import WebhookSource


class PlatformConfiguration(Base, TimestampedMixin):
    """Store platform-specific webhook configurations"""
    
    __tablename__ = "platform_configurations"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    source: Mapped[WebhookSource] = mapped_column(
        SQLEnum(WebhookSource),
        nullable=False,
        unique=True
    )
    
    # Encrypted webhook secret
    webhook_secret: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Platform settings
    api_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Additional endpoints config
    endpoints: Mapped[dict | None] = mapped_column(JSON, nullable=True)