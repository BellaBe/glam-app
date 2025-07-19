# services/billing-service/src/schemas/responses.py
class SubscriptionResponse(BaseModel):
    """Subscription response"""
    id: UUID
    merchant_id: UUID
    shopify_subscription_id: str
    plan_id: str
    plan_name: str
    plan_description: str
    credits_included: int
    price_amount: Decimal
    billing_interval: BillingInterval
    status: SubscriptionStatus
    trial_start_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    activated_at: Optional[datetime]
    next_billing_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    expires_at: Optional[datetime]
    auto_renewal: bool
    proration_enabled: bool
    metadata: dict
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SubscriptionCreateResponse(BaseModel):
    """Subscription creation response"""
    subscription_id: UUID
    confirmation_url: str
    status: SubscriptionStatus
    plan_details: dict
    
    model_config = ConfigDict(from_attributes=True)


class OneTimePurchaseResponse(BaseModel):
    """One-time purchase response"""
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


class BillingPlanResponse(BaseModel):
    """Billing plan response"""
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


class TrialStatusResponse(BaseModel):
    """Trial status response"""
    merchant_id: UUID
    is_trial_active: bool
    trial_start_date: datetime
    trial_end_date: datetime
    days_remaining: int
    total_extensions: int
    total_extension_days: int
    
    model_config = ConfigDict(from_attributes=True)


class TrialExtensionResponse(BaseModel):
    """Trial extension response"""
    success: bool
    extension_id: UUID
    new_trial_end_date: datetime
    total_trial_days: int
    
    model_config = ConfigDict(from_attributes=True)