# services/billing-service/src/schemas/subscription.py
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from ..models import BillingInterval, SubscriptionStatus
from ..schemas.billing_plan import BillingPlanOut

# ---------- IN ---------- #
class SubscriptionIn(BaseModel):
    merchant_id: UUID
    merchant_domain: str = Field(..., max_length=255)
    shopify_subscription_id: str = Field(..., max_length=255)
    shopify_charge_id: str | None = Field(None, max_length=255)
    plan_id: str = Field(..., max_length=100)
    plan_name: str
    plan_description: str | None = None
    credits_included: int = Field(..., ge=0)
    price_amount: Decimal = Field(..., ge=0)
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    trial_start_date: datetime | None = None
    trial_end_date:   datetime | None = None
    auto_renewal: bool = True
    proration_enabled: bool = True
    extra_metadata: dict = {}

    model_config = ConfigDict(extra='forbid')

# ---------- PATCH ---------- #
class SubscriptionPatch(BaseModel):
    plan_id: str | None = Field(None, max_length=100)
    status: SubscriptionStatus | None = None
    cancelled_at: datetime | None = None
    expires_at:   datetime | None = None
    next_billing_date: datetime | None = None
    auto_renewal: bool | None = None
    proration_enabled: bool | None = None

    model_config = ConfigDict(extra='forbid')

# ---------- OUT ---------- #
class SubscriptionOut(BaseModel):
    id: UUID
    merchant_id: UUID
    shopify_subscription_id: str
    plan_id: str
    plan_name: str
    credits_included: int
    price_amount: Decimal
    billing_interval: BillingInterval
    status: SubscriptionStatus
    trial_start_date: datetime | None
    trial_end_date:   datetime | None
    activated_at:    datetime | None
    next_billing_date: datetime | None
    cancelled_at: datetime | None
    expires_at:   datetime | None
    auto_renewal: bool
    proration_enabled: bool
    metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class SubscriptionCreateIn(BaseModel):
    """Payload sent by the storefront to start a new subscription"""
    merchant_id: UUID
    shop_id: str = Field(..., max_length=255)
    plan_id: str = Field(..., max_length=100)
    return_url: str
    test_mode: bool = False

    model_config = ConfigDict(extra="forbid")
    
class SubscriptionCreateOut(BaseModel):
    subscription_id: UUID
    confirmation_url: str
    status: SubscriptionStatus
    plan_details: BillingPlanOut

    model_config = ConfigDict(from_attributes=True)
