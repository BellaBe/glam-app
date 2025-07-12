# services/credit-service/src/repositories/__init__.py
"""Repositories for credit service."""

from .credit_repository import CreditRepository
from .credit_transaction_repository import CreditTransactionRepository

__all__ = [
    "CreditRepository",
    "CreditTransactionRepository",
]
