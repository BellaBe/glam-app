# services/billing-service/src/models/subscription.py
from shared.database.base import Base, TimestampedMixin, MerchantMixin
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Index, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .enums import TrialExtensionReason



class TrialExtension(Base, TimestampedMixin, MerchantMixin):
    """Trial period extensions"""
    
    __tablename__ = "trial_extensions"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Extension Details
    days_added: Mapped[int] = mapped_column(Integer)
    reason: Mapped[TrialExtensionReason] = mapped_column(SQLEnum(TrialExtensionReason), nullable=False)
    extended_by: Mapped[str] = mapped_column(String(255))  # admin_user_id or "system"
    
    # Dates
    original_trial_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    new_trial_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_extension_merchant_created", "merchant_id", "created_at"),
    )