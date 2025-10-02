# services/credit-service/src/schemas/credit.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Output DTOs
class CreditBalanceOut(BaseModel):
    """Credit balance response"""

    balance: int = Field(..., description="Current credit balance")
    total_granted: int = Field(..., description="Total credits ever granted")
    total_consumed: int = Field(..., description="Total credits ever consumed")
    platform_name: str = Field(..., description="Platform name (shopify, etc)")
    domain: str = Field(..., description="Platform domain")

    model_config = ConfigDict(from_attributes=True)


class CreditTransactionOut(BaseModel):
    """Credit transaction history item"""

    id: UUID
    amount: int
    operation: str  # 'credit' or 'debit'
    balance_before: int
    balance_after: int
    reference_type: str
    reference_id: str
    description: str | None = None
    metadata: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListOut(BaseModel):
    """Paginated transaction list"""

    transactions: list[CreditTransactionOut]
    total: int
    page: int
    limit: int
