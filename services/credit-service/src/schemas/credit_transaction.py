# services/credit-service/src/schemas/credit_transaction.py
"""Credit transaction schemas for API requests and responses."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from ..models.credit_transaction import TransactionType, ReferenceType


class CreditTransactionResponse(BaseModel):
    """Credit transaction response schema"""
    
    id: UUID
    merchant_id: UUID
    account_id: UUID
    type: TransactionType = Field(..., description="Type of transaction")
    amount: Decimal = Field(..., description="Amount of credits (always positive)")
    balance_before: Decimal = Field(..., description="Balance before transaction")
    balance_after: Decimal = Field(..., description="Balance after transaction")
    reference_type: ReferenceType = Field(..., description="Reference type")
    reference_id: str = Field(..., description="External reference ID")
    description: str = Field(..., description="Human readable description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CreditTransactionFilter(BaseModel):
    """Filter parameters for transaction queries"""
    
    transaction_type: Optional[TransactionType] = None
    reference_type: Optional[ReferenceType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CreditTransactionCreate(BaseModel):
    """Create credit transaction request (for testing/admin)"""
    
    merchant_id: UUID
    type: TransactionType
    amount: Decimal = Field(..., gt=0, description="Amount must be positive")
    reference_type: ReferenceType
    reference_id: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None
    idempotency_key: str = Field(..., min_length=1, max_length=255)


class BulkTransactionSummary(BaseModel):
    """Summary of transactions for bulk operations"""
    
    total_transactions: int
    total_amount: Decimal
    transaction_types: Dict[str, int]
    date_range: Dict[str, Optional[datetime]]