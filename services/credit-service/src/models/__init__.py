# services/credit-service/src/models/__init__.py
"""Database models for credit service."""

from shared.database.base import Base, TimestampedMixin
from .base import MerchantMixin
from .credit_account import CreditAccount
from .credit_transaction import (
    CreditTransaction, 
    TransactionType, 
    ReferenceType
)

__all__ = [
    # Base (from shared)
    "Base",
    "TimestampedMixin",
    
    # Local mixins
    "MerchantMixin",
    
    # Credit Account
    "CreditAccount",
    
    # Credit Transaction
    "CreditTransaction",
    "TransactionType", 
    "ReferenceType",
]