from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import String, Index, Numeric, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .session import Base


class PaymentStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class ProductType(StrEnum):
    CREDIT_PACK = "credit_pack"


class BillingAccount(Base):
    __tablename__ = "billing_accounts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        unique=True,
        index=True,
        nullable=False
    )
    platform_name: Mapped[str] = mapped_column(String, nullable=False)
    platform_shop_id: Mapped[str] = mapped_column(String, nullable=False)
    platform_domain: Mapped[str] = mapped_column(String, nullable=False)

    # Trial eligibility
    trial_available: Mapped[bool] = mapped_column(default=True, nullable=False)
    trial_activated_at: Mapped[datetime | None] = mapped_column(default=None)

    # Spending stats
    total_spend_usd: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        default=Decimal("0.00"),
        nullable=False
    )
    last_payment_at: Mapped[datetime | None] = mapped_column(default=None)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )


class PricingProduct(Base):
    __tablename__ = "pricing_products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        Index('ix_pricing_products_type_name', 'type', 'name', unique=True),
        Index('ix_pricing_products_active', 'active'),
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        index=True,
        nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    product_type: Mapped[str] = mapped_column(String, nullable=False)
    product_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        String,
        nullable=False,
        default=PaymentStatus.PENDING
    )
    platform_name: Mapped[str] = mapped_column(String, nullable=False)
    platform_charge_id: Mapped[str | None] = mapped_column(
        String,
        unique=True,
        index=True,
        default=None
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    completed_at: Mapped[datetime | None] = mapped_column(default=None)
    expires_at: Mapped[datetime | None] = mapped_column(default=None)
    refunded_at: Mapped[datetime | None] = mapped_column(default=None)

    __table_args__ = (
        Index('ix_payments_merchant_created', 'merchant_id', 'created_at'),
        Index('ix_payments_status', 'status'),
        Index('ix_payments_expires_pending', 'expires_at', postgresql_where=text("status = 'pending'")),
    )
