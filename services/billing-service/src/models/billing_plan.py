
# services/billing-service/src/models/subscription.py
"""Subscription model for billing service."""

from shared.database.base import Base, TimestampedMixin
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, Numeric, JSON, Enum as SQLEnum, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableList, MutableDict
from sqlalchemy.types import JSON

from .enums import BillingInterval


class BillingPlan(Base, TimestampedMixin):
    """Available billing plans"""
    
    __tablename__ = "billing_plans"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # plan_basic, plan_premium
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    credits_included: Mapped[int] = mapped_column(Integer, default=0)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    billing_interval: Mapped[BillingInterval] = mapped_column(
        SQLEnum(BillingInterval), default=BillingInterval.MONTHLY
    )
    
    # Features and Limits
    features: Mapped[List[str]] = mapped_column(MutableList.as_mutable(JSON), default=list)
    credit_rate_per_order: Mapped[int] = mapped_column(Integer, default=1)
    max_monthly_orders: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Availability
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    extra_metadata: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default=dict)

    __table_args__ = (
        Index("idx_plan_active_sort", "is_active", "sort_order"),
    )
