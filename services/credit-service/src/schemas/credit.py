# services/credit-service/src/schemas/credit.py
"""Credit account schemas for API requests and responses."""

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class CreateCredit(BaseModel):
    """Create credit record schema"""
    merchant_id: UUID


class CreditResponse(BaseModel):
    """Credit response schema"""

    id: UUID
    merchant_id: UUID
    balance: int = Field(..., description="Current available credits")
    last_transaction_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)