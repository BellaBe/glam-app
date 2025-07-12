# services/credit-service/src/mappers/credit_transaction_mapper.py
"""Mapper for credit transaction model to response schemas."""

from typing import Dict, Any
from uuid import UUID

from shared.mappers import BaseMapper
from ..models.credit_transaction import CreditTransaction
from ..schemas.credit_transaction import (
    CreditTransactionCreate,
    CreditTransactionResponse,
    TransactionStatsByMerchantIdResponse
)


class CreditTransactionMapper(BaseMapper[CreditTransaction, CreditTransactionCreate, None, CreditTransactionResponse]): # type: ignore
    """
    Maps between credit transaction model and response schemas.
    """
    __slots__ = ()  # Memory optimization
    
    def create_to_model(
        self, 
        create_schema: CreditTransactionCreate,
        **kwargs: Any  # Additional arguments for model creation (if needed)
    ) -> CreditTransaction:
        """
        Convert create schema to credit transaction model.
        
        Args:
            create_schema: The create request schema
            **kwargs: Additional arguments for model creation
            
        Returns:
            CreditTransaction model instance
        """
        
        balance_before = kwargs.get("balance_before", None)
        balance_after = kwargs.get("balance_after", None)
        credit_id = kwargs.get("credit_id", None)
        idempotency_key = kwargs.get("idempotency_key", None)

        if credit_id is None:
            raise ValueError("credit_id must be provided")
        
        if balance_before is None or balance_after is None:
            raise ValueError("balance_before and balance_after must be provided")
        
        if not idempotency_key:
            raise ValueError("idempotency_key must be provided")
        
        extra_metadata = kwargs.get("extra_metadata", {})
        
        return CreditTransaction(
            merchant_id=create_schema.merchant_id,
            credit_id=UUID(),
            operation_type=create_schema.operation_type,
            transaction_type=create_schema.transaction_type,
            credits_used=create_schema.credits_to_use,
            balance_before=balance_before,
            balance_after=balance_after,
            idempotency_key=idempotency_key,
            extra_metadata=extra_metadata,
        )
    
    def model_to_response(self, model: CreditTransaction) -> CreditTransactionResponse:
        """
        Convert credit transaction model to response schema.
        
        Args:
            model: The credit transaction model instance
            
        Returns:
            Credit transaction response schema
        """
        return CreditTransactionResponse(
            id=model.id,
            merchant_id=model.merchant_id,
            credit_id=model.credit_id,
            operation_type=model.operation_type,
            transaction_type=model.transaction_type,
            credits_used=model.credits_used,
            balance_before=model.balance_before,
            balance_after=model.balance_after,
            idempotency_key=model.idempotency_key,
            extra_metadata=model.extra_metadata,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    
    def to_stats_response(
        self,
        merchant_id: UUID,
        stats_data: Dict[str, Any]
    ) -> TransactionStatsByMerchantIdResponse:
        """
        Convert stats dictionary to response schema.
        
        Args:
            merchant_id: The merchant identifier
            stats_data: Dictionary containing transaction statistics
            
        Returns:
            Transaction statistics response schema
        """
        transactions = stats_data.get("transactions", [])
        if transactions and isinstance(transactions[0], CreditTransaction):
            # Convert model instances to response schemas
            transaction_responses = self.models_to_responses(transactions)
        else:
            # Assume already converted or empty
            transaction_responses = transactions
            
        return TransactionStatsByMerchantIdResponse(
            merchant_id=merchant_id,
            total_increases=stats_data.get("total_increases", 0),
            total_decreases=stats_data.get("total_decreases", 0),
            transaction_count=stats_data.get("transaction_count", 0),
            last_transaction_at=stats_data.get("last_transaction_at"),
        )