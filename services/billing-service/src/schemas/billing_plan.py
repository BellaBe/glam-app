# services/billing-service/src/schemas/billing_plan.py
"""Schemas for billing plans."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from ..models import BillingInterval

# ---------- IN ---------- #
class BillingPlanIn(BaseModel):
    id: str = Field(..., max_length=100)          # e.g. "plan_basic"
    name: str = Field(..., max_length=255)
    description: str = Field(..., max_length=1000)
    credits_included: int = Field(..., ge=0)
    price_amount: Decimal = Field(..., ge=0)
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    features: List[str] = []
    credit_rate_per_order: int = Field(1, ge=1)
    max_monthly_orders: Optional[int] = Field(None, ge=1)
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = 0

    model_config = ConfigDict(extra="forbid")

# ---------- PATCH ---------- #
class BillingPlanPatch(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    price_amount: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None
    is_featured: bool | None = None
    sort_order: int | None = None

    model_config = ConfigDict(extra="forbid")

# ---------- OUT ---------- #
class BillingPlanOut(BaseModel):
    id: str
    name: str
    description: str
    credits_included: int
    price_amount: Decimal
    billing_interval: BillingInterval
    features: List[str]
    credit_rate_per_order: int
    max_monthly_orders: Optional[int]
    is_active: bool
    is_featured: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)