
# services/billing-service/src/models/one_time_purchase.py
from shared.database.base import Base, TimestampedMixin, MerchantMixin
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Numeric, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.mutable import MutableDict


class PurchaseStatus(str, Enum):
    PENDING = "PENDING"           # Charge created but not completed
    COMPLETED = "COMPLETED"       # Payment successful
    CANCELLED = "CANCELLED"       # Charge cancelled
    FAILED = "FAILED"             # Payment failed


class OneTimePurchase(Base, TimestampedMixin, MerchantMixin):
    """One-time credit purchases"""
    
    __tablename__ = "one_time_purchases"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Shopify Integration
    shopify_charge_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Purchase Details
    credits_purchased: Mapped[int] = mapped_column(Integer, default=0)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    description: Mapped[str] = mapped_column(String(500))
    
    # Status
    status: Mapped[PurchaseStatus] = mapped_column(SQLEnum(PurchaseStatus), default=PurchaseStatus.PENDING, index=True)

    # Timestamps
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    extra_metadata: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default=dict)
    
    __table_args__ = (
        Index("idx_purchase_merchant_status", "merchant_id", "status"),
        Index("idx_purchase_shopify_id", "shopify_charge_id"),
    )
