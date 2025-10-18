# services/billing-service/src/schemas/billing.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PaymentStatusType = Literal["pending", "completed", "failed", "expired", "refunded"]
ProductTypeType = Literal["credit_pack"]


class TrialStatusOut(BaseModel):
    """Trial status response"""
    available: bool
    activated_at: datetime | None = None


class ProductOut(BaseModel):
    """Pricing product output"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    name: str
    price: Decimal
    currency: str
    metadata: dict
    active: bool


class CreateChargeIn(BaseModel):
    """Create charge request"""
    product_id: str = Field(..., description="Product ID to purchase")
    return_url: str = Field(..., description="URL to redirect after payment")
    platform: str = Field(..., description="Platform name (e.g., 'shopify')")


class CreateChargeOut(BaseModel):
    """Create charge response"""
    payment_id: UUID
    checkout_url: str


class PaymentOut(BaseModel):
    """Payment details output"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    amount: Decimal
    currency: str
    description: str
    product_type: str
    product_id: str
    status: PaymentStatusType
    platform_name: str
    platform_charge_id: str | None
    metadata: dict | None
    created_at: datetime
    completed_at: datetime | None
    expires_at: datetime | None
    refunded_at: datetime | None


class BillingAccountOut(BaseModel):
    """Billing account output"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    trial_available: bool
    trial_activated_at: datetime | None
    total_spend_usd: Decimal
    last_payment_at: datetime | None
    created_at: datetime
    updated_at: datetime
