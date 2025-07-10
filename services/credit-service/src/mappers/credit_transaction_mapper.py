# services/credit-service/src/mappers/credit_transaction_mapper.py
"""Mapper for credit transaction model to response schemas."""

from typing import List
from ..models.credit_transaction import CreditTransaction
from ..schemas.credit_transaction import CreditTransactionResponse


class CreditTransactionMapper:
    """Maps between credit transaction model and response schemas"""
    
    @staticmethod
    def to_response(transaction: CreditTransaction) -> CreditTransactionResponse:
        """Convert credit transaction model to response schema"""
        return CreditTransactionResponse(
            id=transaction.id,
            merchant_id=transaction.merchant_id,
            account_id=transaction.account_id,
            type=transaction.type,
            amount=transaction.amount,
            balance_before=transaction.balance_before,
            balance_after=transaction.balance_after,
            reference_type=transaction.reference_type,
            reference_id=transaction.reference_id,
            description=transaction.description,
            metadata=transaction.metadata,
            created_at=transaction.created_at
        )
    
    @staticmethod
    def to_response_list(transactions: List[CreditTransaction]) -> List[CreditTransactionResponse]:
        """Convert list of credit transactions to response list"""
        return [CreditTransactionMapper.to_response(tx) for tx in transactions]