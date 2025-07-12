# services/credit-service/src/models/credit_transaction.py
"""Simplified credit transaction model."""

from enum import Enum
from uuid import UUID, uuid4
from sqlalchemy import String, Integer, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from shared.database.base import TimestampedMixin, MerchantMixin, Base


class OperationType(str, Enum):
    """Types of credit transactions"""
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"


class TransactionType(str, Enum):
    """Reference types for transactions"""
    ORDER_PAID = "ORDER_PAID"
    SUBSCRIPTION = "SUBSCRIPTION" 
    TRIAL = "TRIAL"
    MANUAL = "MANUAL"


class CreditTransaction(Base, TimestampedMixin, MerchantMixin):
    """Record of all credit operations for audit trail"""
    
    __tablename__ = "credit_transactions"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    credit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    # Transaction details
    operation_type: Mapped[OperationType] = mapped_column(
        SQLEnum(OperationType),
        nullable=False,
        index=True
    )
    
    credits_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    balance_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType),
        nullable=False,
        index=True
    )
    
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )
    
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique reference ID that serves as idempotency key"
    )
    
    # Performance indexes
    __table_args__ = (
        Index("idx_merchant_type", "merchant_id", "transaction_type"),
        Index("idx_merchant_created", "merchant_id", "created_at"),
        Index("idx_credit_created", "credit_id", "created_at"),
    )