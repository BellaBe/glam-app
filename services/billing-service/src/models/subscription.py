
# services/billing-service/src/models/subscription.py
from shared.database.base import Base, TimestampedMixin, MerchantMixin
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Numeric, JSON, Enum as SQLEnum, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.mutable import MutableDict  
from .enums import BillingInterval
    
class SubscriptionStatus(str, Enum):
    PENDING = "PENDING"           # Created but not yet charged
    ACTIVE = "ACTIVE"             # Successfully charged and active
    CANCELLED = "CANCELLED"       # Cancelled by merchant or admin
    EXPIRED = "EXPIRED"           # Billing failed or expired
    FROZEN = "FROZEN"             # Temporarily suspended


class Subscription(Base, TimestampedMixin, MerchantMixin):
    """Subscription model for recurring billing"""
    
    __tablename__ = "subscriptions"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Shopify Integration
    shopify_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    shopify_charge_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    # Plan Details
    plan_id: Mapped[str] = mapped_column(String(100), index=True)
    plan_name: Mapped[str] = mapped_column(String(255))
    plan_description: Mapped[str] = mapped_column(Text)
    credits_included: Mapped[int] = mapped_column(Integer, default=0)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    billing_interval: Mapped[BillingInterval] = mapped_column(SQLEnum(BillingInterval), default=BillingInterval.MONTHLY)

    # Status Management
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING, index=True
    )
    
    # Billing Cycle
    trial_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_billing_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Configuration
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=True)
    proration_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    extra_metadata: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default=dict)

    __table_args__ = (
        Index("idx_subscription_merchant_status", "merchant_id", "status"),
        Index("idx_subscription_shopify_id", "shopify_subscription_id"),
        Index("idx_subscription_next_billing", "next_billing_date"),
    )
