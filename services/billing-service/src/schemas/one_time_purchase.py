# services/billing-service/src/schemas/one_time_purchase.py
"""Schemas for one-time purchase model."""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional
from ..models import PurchaseStatus

# ---------- IN ---------- #
class OneTimePurchaseIn(BaseModel):
    merchant_id: UUID
    merchant_domain: str = Field(..., max_length=255)
    shopify_charge_id: str = Field(..., max_length=255)
    credits_purchased: int = Field(..., ge=1)
    price_amount: Decimal = Field(..., ge=0)
    description: str = Field(..., max_length=500)
    status: PurchaseStatus = PurchaseStatus.PENDING
    completed_at: Optional[datetime] = None
    extra_metadata: dict = {}

    model_config = ConfigDict(extra="forbid")

# ---------- OUT ---------- #
class OneTimePurchaseOut(BaseModel):
    id: UUID
    merchant_id: UUID
    shopify_charge_id: str
    credits_purchased: int
    price_amount: Decimal
    description: str
    status: PurchaseStatus
    completed_at: Optional[datetime]
    metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
