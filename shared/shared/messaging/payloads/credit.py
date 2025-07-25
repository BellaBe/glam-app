# shared/messaging/payloads/credit.py

from pydantic import BaseModel, Field
from uuid import UUID


class CreditDeductionRequestedPayload(BaseModel):
    """Request to deduct credits"""
    merchant_id: UUID
    credits_to_deduct: int = Field(..., gt=0)
    operation_type: str
    operation_id: UUID
    requested_by: str


class CreditDeductedPayload(BaseModel):
    """Credits deducted successfully"""
    merchant_id: UUID
    credits_deducted: int = Field(..., gt=0)
    previous_balance: int = Field(..., ge=0)
    new_balance: int = Field(..., ge=0)
    operation_type: str
    operation_id: UUID