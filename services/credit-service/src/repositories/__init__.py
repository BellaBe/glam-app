# services/credit-service/src/repositories/__init__.py
"""Repositories for credit service."""

from .credit_account_repository import CreditAccountRepository
from .credit_transaction_repository import CreditTransactionRepository

__all__ = [
    "CreditAccountRepository",
    "CreditTransactionRepository", 
]