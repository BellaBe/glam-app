# services/billing-service/src/models/__init__.py
from shared.database.base import Base, TimestampedMixin, MerchantMixin
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, Numeric, JSON, Enum as SQLEnum, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID


# Enums
class SubscriptionStatus(str, Enum):
    PENDING = "PENDING"           # Created but not yet charged
    ACTIVE = "ACTIVE"             # Successfully charged and active
    CANCELLED = "CANCELLED"       # Cancelled by merchant or admin
    EXPIRED = "EXPIRED"           # Billing failed or expired
    FROZEN = "FROZEN"             # Temporarily suspended


class PurchaseStatus(str, Enum):
    PENDING = "PENDING"           # Charge created but not completed
    COMPLETED = "COMPLETED"       # Payment successful
    CANCELLED = "CANCELLED"       # Charge cancelled
    FAILED = "FAILED"             # Payment failed


class BillingInterval(str, Enum):
    MONTHLY = "EVERY_30_DAYS"     # Shopify monthly interval
    ANNUAL = "ANNUAL"             # Shopify annual interval


class TrialExtensionReason(str, Enum):
    SUPPORT_REQUEST = "support_request"
    TECHNICAL_ISSUE = "technical_issue"
    ONBOARDING_ASSISTANCE = "onboarding_assistance"
    ADMIN_DISCRETION = "admin_discretion"


# Models
class Subscription(Base, TimestampedMixin, MerchantMixin):
    """Subscription model for recurring billing"""
    
    __tablename__ = "subscriptions"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Shopify Integration
    shopify_subscription_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    shopify_charge_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    
    # Plan Details
    plan_id: Mapped[str] = mapped_column(String(100), index=True)
    plan_name: Mapped[str] = mapped_column(String(255))
    plan_description: Mapped[str] = mapped_column(Text)
    credits_included: Mapped[int] = mapped_column(Integer, default=0)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    billing_interval: Mapped[BillingInterval] = mapped_column(
        SQLEnum(BillingInterval), default=BillingInterval.MONTHLY
    )
    
    # Status Management
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING, index=True
    )
    
    # Billing Cycle
    trial_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_billing_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Configuration
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=True)
    proration_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    __table_args__ = (
        Index("idx_subscription_merchant_status", "merchant_id", "status"),
        Index("idx_subscription_shopify_id", "shopify_subscription_id"),
        Index("idx_subscription_next_billing", "next_billing_date"),
    )


class OneTimePurchase(Base, TimestampedMixin, MerchantMixin):
    """One-time credit purchases"""
    
    __tablename__ = "one_time_purchases"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Shopify Integration
    shopify_charge_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    
    # Purchase Details
    credits_purchased: Mapped[int] = mapped_column(Integer, default=0)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    description: Mapped[str] = mapped_column(String(500))
    
    # Status
    status: Mapped[PurchaseStatus] = mapped_column(
        SQLEnum(PurchaseStatus), default=PurchaseStatus.PENDING, index=True
    )
    
    # Timestamps
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    __table_args__ = (
        Index("idx_purchase_merchant_status", "merchant_id", "status"),
        Index("idx_purchase_shopify_id", "shopify_charge_id"),
    )


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
    features: Mapped[List[str]] = mapped_column(JSON, default=list)
    credit_rate_per_order: Mapped[int] = mapped_column(Integer, default=1)
    max_monthly_orders: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Availability
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    __table_args__ = (
        Index("idx_plan_active_sort", "is_active", "sort_order"),
    )


class TrialExtension(Base, TimestampedMixin, MerchantMixin):
    """Trial period extensions"""
    
    __tablename__ = "trial_extensions"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Extension Details
    days_added: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(100))
    extended_by: Mapped[str] = mapped_column(String(255))  # admin_user_id or "system"
    
    # Dates
    original_trial_end: Mapped[datetime] = mapped_column(DateTime)
    new_trial_end: Mapped[datetime] = mapped_column(DateTime)
    
    __table_args__ = (
        Index("idx_extension_merchant_created", "merchant_id", "created_at"),
    )
