# services/billing-service/src/schemas/requests.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID


class SubscriptionCreateRequest(BaseModel):
    """Create subscription request"""
    merchant_id: UUID
    shop_id: str = Field(..., min_length=1, max_length=255)
    plan_id: str = Field(..., min_length=1, max_length=100)
    return_url: str = Field(..., min_length=1, max_length=500)
    test_mode: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class SubscriptionUpdateRequest(BaseModel):
    """Update subscription request"""
    plan_id: Optional[str] = Field(None, min_length=1, max_length=100)
    proration_behavior: str = Field(default="CREATE_PRORATIONS")
    
    model_config = ConfigDict(from_attributes=True)


class OneTimePurchaseCreateRequest(BaseModel):
    """Create one-time purchase request"""
    merchant_id: UUID
    shop_id: str = Field(..., min_length=1, max_length=255)
    credits: int = Field(..., ge=1, le=10000)
    return_url: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=500)
    
    model_config = ConfigDict(from_attributes=True)


class TrialExtensionRequest(BaseModel):
    """Trial extension request"""
    additional_days: int = Field(..., ge=1, le=30)
    reason: TrialExtensionReason
    extended_by: str = Field(..., min_length=1, max_length=255)
    
    model_config = ConfigDict(from_attributes=True)


class BillingPlanRequest(BaseModel):
    """Billing plan create/update request"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=1000)
    credits_included: int = Field(..., ge=0)
    price_amount: Decimal = Field(..., ge=0)
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    features: List[str] = Field(default_factory=list)
    credit_rate_per_order: int = Field(default=1, ge=1)
    max_monthly_orders: Optional[int] = Field(None, ge=1)
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = 0
    
    model_config = ConfigDict(from_attributes=True)