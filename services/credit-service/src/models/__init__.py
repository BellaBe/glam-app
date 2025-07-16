# services/credit-service/src/models/__init__.py
"""Database models for credit service."""

from shared.database.base import Base, TimestampedMixin
from shared.database.base import MerchantMixin
from .credit import Credit
from .credit_transaction import CreditTransaction, TransactionType

__all__ = [
    # Base (from shared)
    "Base",
    "TimestampedMixin",
    # Local mixins
    "MerchantMixin",
    # Credit Account
    "Credit",
    # Credit Transaction
    "CreditTransaction",
    "TransactionType",
]
