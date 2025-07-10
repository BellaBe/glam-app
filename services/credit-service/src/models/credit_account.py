# services/credit-service/src/models/credit_account.py
"""Credit account model for managing merchant credit balances."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import DECIMAL, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from shared.database.base import TimestampedMixin, MerchantMixin, Base


class CreditAccount(Base, TimestampedMixin, MerchantMixin):
    """Credit account for each merchant"""
    
    __tablename__ = "credit_accounts"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    # Credit balances - using DECIMAL for precision
    balance: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=2),
        nullable=False,
        default=Decimal("0.00"),
        index=True
    )
    
    lifetime_credits: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2),
        nullable=False,
        default=Decimal("0.00")
    )
    
    # Tracking
    last_recharge_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_merchant_balance", "merchant_id", "balance"),
        Index("idx_merchant_created", "merchant_id", "created_at"),
    )