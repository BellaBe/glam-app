# services/merchant-service/src/models/installation_record.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, JSON, Index
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import Optional, Dict, Any, List
from .merchant import Merchant
from shared.database.base import Base, TimestampedMixin

class InstallationRecord(Base, TimestampedMixin):
    """Platform installation record"""
    __tablename__ = "installation_records"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    merchant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("merchants.id"), index=True, nullable=False)
    
    # Platform-agnostic core
    platform: Mapped[str] = mapped_column(String(50), default="shopify")
    installed_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    uninstalled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    install_channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    installed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    installation_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Versions & permissions
    app_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    platform_api_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    permissions_granted: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    callbacks_configured: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    
    # Marketing context
    referral_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Platform-specific data
    platform_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Uninstallation tracking
    uninstall_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    uninstall_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uninstall_feedback: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Relationships
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="installation_records")
    
    # Composite index (created via Alembic migration)
    __table_args__ = (
        Index("idx_installation_merchant_platform", "merchant_id", "platform"),
        Index("idx_installation_platform_installed", "platform", "installed_at"),
    )