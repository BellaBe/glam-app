# services/credit-service/src/models/credit_transaction.py
"""Credit transaction model for audit trail."""

from enum import Enum
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DECIMAL, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from shared.database.base import TimestampedMixin, MerchantMixin, Base


class TransactionType(str, Enum):
    """Types of credit transactions"""
    RECHARGE = "RECHARGE"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"


class ReferenceType(str, Enum):
    """Reference types for transactions"""
    ORDER_PAID = "ORDER_PAID"
    BILLING_PAYMENT = "BILLING_PAYMENT"
    SUBSCRIPTION = "SUBSCRIPTION"
    TRIAL = "TRIAL"
    MANUAL = "MANUAL"
    ORDER_REFUND = "ORDER_REFUND"


class CreditTransaction(Base, TimestampedMixin, MerchantMixin):
    """Record of all credit operations for audit trail"""
    
    __tablename__ = "credit_transactions"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    # Transaction details
    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType),
        nullable=False,
        index=True
    )
    
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=2),
        nullable=False
    )
    
    # Balance tracking
    balance_before: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=2),
        nullable=False
    )
    
    balance_after: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=2),
        nullable=False
    )
    
    # Reference information
    reference_type: Mapped[ReferenceType] = mapped_column(
        SQLEnum(ReferenceType),
        nullable=False,
        index=True
    )
    
    reference_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    # Additional context
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Idempotency
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Performance indexes
    __table_args__ = (
        Index("idx_merchant_type", "merchant_id", "type"),
        Index("idx_merchant_created", "merchant_id", "created_at"),
        Index("idx_reference", "reference_type", "reference_id"),
        Index("idx_account_created", "account_id", "created_at"),
    )