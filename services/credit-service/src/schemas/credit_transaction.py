# services/credit-service/src/schemas/credit_transaction.py
"""Credit transaction schemas for API requests and responses."""

from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from ..models.credit_transaction import TransactionType, OperationType

class CreditTransactionCreate(BaseModel):
    """Request schema for creating a credit transaction"""
    
    merchant_id: UUID
    operation_type: OperationType = Field(..., description="INCREASE or DECREASE")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    credits_to_use: int = Field(..., gt=0, description="Credits used for transaction")

class CreditTransactionResponse(BaseModel):
    """Credit transaction response schema"""
    
    id: UUID
    merchant_id: UUID
    credit_id: UUID
    operation_type: OperationType = Field(..., description="INCREASE or DECREASE")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    credits_used: int = Field(..., description="Credits used for transaction")
    balance_before: int = Field(..., description="Balance before transaction")
    balance_after: int = Field(..., description="Balance after transaction")
    idempotency_key: str = Field(..., description="Unique idempotency key")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CreditTransactionListResponse(BaseModel):
    """Response schema for listing credit transactions"""
    
    transactions: list[CreditTransactionResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool


class TransactionStatsByMerchantIdResponse(BaseModel):
    """Response schema for transaction statistics"""
    
    merchant_id: UUID
    total_increases: int
    total_decreases: int
    transaction_count: int
    last_transaction_at: Optional[datetime]
   