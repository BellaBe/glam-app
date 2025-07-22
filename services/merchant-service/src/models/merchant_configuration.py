# services/merchant-service/src/models/merchant_configuration.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, Text
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import Optional, Dict, Any
from shared.database.base import Base, TimestampedMixin

from .merchant import Merchant

class MerchantConfiguration(Base, TimestampedMixin):
    """Merchant configuration model"""
    __tablename__ = "merchant_configurations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    merchant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("merchants.id"), index=True, nullable=False)
    
    # Legal Compliance
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    terms_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    terms_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    privacy_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    privacy_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    privacy_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Widget Settings (UI-only, read by frontend)
    widget_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    widget_position: Mapped[str] = mapped_column(String(50), default="bottom-right")
    widget_theme: Mapped[str] = mapped_column(String(50), default="light")
    widget_language: Mapped[str] = mapped_column(String(10), default="auto")
    widget_configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Technical Settings
    api_rate_limits: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    webhook_configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    integration_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Custom Branding (UI-only)
    custom_css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_branding: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    custom_messages: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Cross-Service Coordination
    is_marketable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="configuration")