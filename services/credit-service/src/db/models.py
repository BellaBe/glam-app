# services/credit-service/src/db/models.py

from __future__ import annotations
from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, Boolean, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .session import Base


class CreditAccount(Base):
    __tablename__ = "credit_accounts"

    id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    merchant_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)

    # Platform context
    platform_name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_domain: Mapped[str] = mapped_column(String(255), nullable=False)

    # Current balances (never negative)
    trial_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    purchased_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Lifetime tracking
    total_granted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_consumed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Trial runtime state
    trial_credits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index("ix_credit_accounts_merchant_id", "merchant_id"),
        Index("ix_credit_accounts_platform_domain", "platform_domain"),
        Index("ix_credit_accounts_platform_name_id", "platform_name", "platform_id"),
    )

    @property
    def trial_exhausted(self) -> bool:
        """Derived property instead of stored field"""
        return self.trial_credits == 0
    
class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), nullable=False)
    merchant_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Transaction details (amount always positive)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)  # 'credit' | 'debit'
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # 'trial' | 'purchase' | 'refund'

    # Total balance snapshots
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)

    # Breakdown snapshots for debugging
    trial_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trial_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchased_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchased_after: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Idempotency key
    reference_type: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index("ix_credit_transactions_merchant_created", "merchant_id", "created_at"),
        UniqueConstraint("reference_type", "reference_id", name="uq_credit_transactions_reference"),
    )
