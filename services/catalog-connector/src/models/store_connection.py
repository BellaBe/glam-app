"""Store connection model and related enums."""

from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from sqlalchemy import String, Enum as SQLEnum, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from shared.database.base import Base, TimestampedMixin
from .base import EncryptedFieldMixin


class StoreStatus(str, Enum):
    """Store connection status."""
    ACTIVE = "ACTIVE"
    INVALID = "INVALID"
    DISCONNECTED = "DISCONNECTED"


class StoreConnection(Base, TimestampedMixin, EncryptedFieldMixin):
    """Store connection details."""
    
    __tablename__ = "store_connections"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )
    
    # Store identification
    store_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Shopify details
    shopify_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="e.g., myshop.myshopify.com"
    )
    
    # Encrypted access token
    _access_token: Mapped[str] = mapped_column(
        "access_token",
        Text,
        nullable=False
    )
    
    # API configuration
    api_version: Mapped[str] = mapped_column(
        String(10),
        default="2024-01",
        nullable=False
    )
    
    # Webhook configuration (for future use)
    webhook_secret: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    # Status
    status: Mapped[StoreStatus] = mapped_column(
        SQLEnum(StoreStatus),
        default=StoreStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Activity tracking
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    @hybrid_property
    def access_token(self) -> str:
        """Get decrypted access token."""
        return self.decrypt(self._access_token)
    
    @access_token.setter
    def access_token(self, value: str):
        """Set encrypted access token."""
        self._access_token = self.encrypt(value)
    
    def __repr__(self) -> str:
        return f"<StoreConnection(store_id={self.store_id}, domain={self.shopify_domain}, status={self.status})>"
