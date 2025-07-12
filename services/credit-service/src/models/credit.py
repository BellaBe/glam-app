# services/credit-service/src/models/credit.py
"""Credit account model for managing merchant credit balances."""

from uuid import UUID, uuid4
from sqlalchemy import Index, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from shared.database.base import TimestampedMixin, MerchantMixin, Base


class Credit(Base, TimestampedMixin, MerchantMixin):
    """Credit account for each merchant"""

    __tablename__ = "credits"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Credit balances
    balance: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )
    
    last_transaction_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_merchant_balance", "merchant_id", "balance"),
        Index("idx_merchant_created", "merchant_id", "created_at"),
    )
