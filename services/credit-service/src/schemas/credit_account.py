# services/credit-service/src/schemas/credit_account.py
"""Credit account schemas for API requests and responses."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CreditAccountResponse(BaseModel):
    """Credit account response schema"""
    
    id: UUID
    merchant_id: UUID
    balance: Decimal = Field(..., description="Current available credits")
    lifetime_credits: Decimal = Field(..., description="Total credits ever received")
    last_recharge_at: Optional[datetime] = Field(None, description="Last time credits were added")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CreditAccountSummary(BaseModel):
    """Credit account summary for quick responses"""
    
    merchant_id: UUID
    balance: Decimal
    last_recharge_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)