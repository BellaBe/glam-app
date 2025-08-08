from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

# Enums matching Prisma schema
class SubscriptionStatus(str, Enum):
    none = "none"
    active = "active"
    pending = "pending"
    paused = "paused"
    cancelled = "cancelled"
    expired = "expired"

class PlanKind(str, Enum):
    subscription = "subscription"
    one_time = "one_time"

class BillingInterval(str, Enum):
    month = "month"
    year = "year"

class TrialStatus(str, Enum):
    never_started = "never_started"
    active = "active"
    expired = "expired"

# ---------- BILLING PLAN DTOs ----------
class BillingPlanOut(BaseModel):
    """Output DTO for billing plan"""
    id: str
    shopifyHandle: str
    kind: PlanKind
    name: str
    description: str
    price: Decimal
    currency: str
    billingInterval: Optional[BillingInterval] = None
    ctaLabel: Optional[str] = None
    sortOrder: int
    active: bool
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

# ---------- TRIAL DTOs ----------
class TrialCreateIn(BaseModel):
    """Input DTO for creating trial"""
    days: Optional[int] = Field(None, ge=1, le=90)
    
    model_config = ConfigDict(extra="forbid")

class TrialOut(BaseModel):
    """Output DTO for trial"""
    status: TrialStatus
    trialEndsAt: Optional[datetime] = None
    remainingDays: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class TrialExtendIn(BaseModel):
    """Input DTO for extending trial"""
    shopDomain: str
    days: int = Field(..., ge=1, le=90)
    
    model_config = ConfigDict(extra="forbid")

# ---------- REDIRECT DTOs ----------
class RedirectCreateIn(BaseModel):
    """Input DTO for creating redirect"""
    plan: str
    returnUrl: Optional[HttpUrl] = None
    
    model_config = ConfigDict(extra="forbid")

class RedirectOut(BaseModel):
    """Output DTO for redirect"""
    redirectUrl: str

# ---------- ENTITLEMENTS DTOs ----------
class EntitlementSource(str, Enum):
    subscription = "subscription"
    trial = "trial"
    none = "none"

class EntitlementReason(str, Enum):
    trial_expired = "trial_expired"
    no_subscription = "no_subscription"
    subscription_cancelled = "subscription_cancelled"

class EntitlementsOut(BaseModel):
    """Output DTO for entitlements"""
    trialActive: bool
    subscriptionActive: bool
    entitled: bool
    source: EntitlementSource
    reason: Optional[EntitlementReason] = None
    trialEndsAt: Optional[datetime] = None
    currentPeriodEnd: Optional[datetime] = None

# ---------- STATE DTOs ----------
class BillingStateOut(BaseModel):
    """Output DTO for billing state"""
    status: SubscriptionStatus
    planId: Optional[str] = None
    planName: Optional[str] = None
    planHandle: Optional[str] = None
    trial: Dict[str, Any]
    currentPeriodEnd: Optional[datetime] = None
    lastUpdatedAt: datetime

# ---------- PLAN LIST DTOs ----------
class PlansListOut(BaseModel):
    """Output DTO for plans list with trial status"""
    plans: List[BillingPlanOut]
    trialUsed: bool

# ---------- RECONCILIATION DTOs ----------
class ReconcileIn(BaseModel):
    """Input DTO for reconciliation"""
    shopDomain: str
    
    model_config = ConfigDict(extra="forbid")

class ReconcileOut(BaseModel):
    """Output DTO for reconciliation result"""
    updated: bool
    changes: Optional[Dict[str, Any]] = None

# ---------- EVENT PAYLOADS ----------
class TrialActivatedPayload(BaseModel):
    """Payload for trial activated event"""
    shopDomain: str
    merchantId: Optional[UUID] = None
    endsAt: datetime
    days: int
    activatedAt: datetime
    correlationId: Optional[str] = None

class TrialExpiredPayload(BaseModel):
    """Payload for trial expired event"""
    shopDomain: str
    merchantId: Optional[UUID] = None
    expiredAt: datetime
    correlationId: Optional[str] = None

class SubscriptionChangedPayload(BaseModel):
    """Payload for subscription changed event"""
    shopDomain: str
    merchantId: Optional[UUID] = None
    status: SubscriptionStatus
    planId: Optional[str] = None
    planHandle: Optional[str] = None
    currentPeriodEnd: Optional[datetime] = None
    source: Literal["webhook", "reconciliation", "manual"]
    correlationId: Optional[str] = None

class SubscriptionActivatedPayload(BaseModel):
    """Payload for subscription activated event"""
    shopDomain: str
    merchantId: Optional[UUID] = None
    planId: str
    planHandle: str
    correlationId: Optional[str] = None

class SubscriptionCancelledPayload(BaseModel):
    """Payload for subscription cancelled event"""
    shopDomain: str
    merchantId: Optional[UUID] = None
    cancelAt: Optional[datetime] = None
    reason: Optional[str] = None
    correlationId: Optional[str] = None

class CreditsGrantPayload(BaseModel):
    """Payload for credits grant event"""
    shopDomain: str
    merchantId: Optional[UUID] = None
    credits: int
    reason: Literal["one_time_pack"]
    externalRef: str
    correlationId: Optional[str] = None

# ---------- WEBHOOK PAYLOADS ----------
class AppSubscriptionUpdatedPayload(BaseModel):
    """Webhook payload for app subscription updated"""
    shop_domain: str
    subscription_id: str
    status: str
    test: bool = False
    current_period_end: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    plan_handle: Optional[str] = None
    webhook_id: str

class AppPurchaseUpdatedPayload(BaseModel):
    """Webhook payload for app purchase updated"""
    shop_domain: str
    charge_id: str
    status: str
    test: bool = False
    credits: Optional[int] = None
    webhook_id: str

class AppUninstalledPayload(BaseModel):
    """Webhook payload for app uninstalled"""
    shop_domain: str
    webhook_id: str

