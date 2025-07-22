# services/merchant-service/src/models/merchant_status.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, JSON
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import Optional, List
from shared.database.base import Base, TimestampedMixin
from .enums import MerchantStatusEnum

from .merchant import Merchant

class MerchantStatus(Base, TimestampedMixin):
    """Merchant status model"""
    __tablename__ = "merchant_statuses"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    merchant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("merchants.id"), index=True, nullable=False)
    
    # Core Status Management
    status: Mapped[MerchantStatusEnum] = mapped_column(String(50), index=True, nullable=False)
    previous_status: Mapped[Optional[MerchantStatusEnum]] = mapped_column(String(50), nullable=True)
    status_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status Timestamps
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # High-Level Activity Tracking
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Status History
    status_history: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    
    # Relationships
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="status")
