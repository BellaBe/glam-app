
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from enum import Enum


# ---------- ENUMS ----------
class CreditPack(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class Platform(str, Enum):
    SHOPIFY = "shopify"
    STRIPE = "stripe"
    CUSTOM = "custom"


class PurchaseStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


# ---------- INPUT DTOs ----------
class TrialActivateIn(BaseModel):
    """Input for activating trial"""
    idempotency_key: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class PurchaseCreateIn(BaseModel):
    """Input for creating credit purchase"""
    pack: CreditPack
    platform: Platform
    return_url: str
    idempotency_key: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


# ---------- OUTPUT DTOs ----------
class TrialStatusOut(BaseModel):
    """Trial status response"""
    available: bool
    active: bool
    ends_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class TrialActivatedOut(BaseModel):
    """Trial activation response"""
    success: bool = True
    ends_at: datetime
    credits_granted: int
    model_config = ConfigDict(from_attributes=True)


class PurchaseOut(BaseModel):
    """Credit purchase response"""
    id: UUID
    merchant_id: UUID
    credits: int
    amount: str
    status: PurchaseStatus
    platform: Optional[str] = None
    platform_charge_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PurchaseCreatedOut(BaseModel):
    """Purchase creation response"""
    purchase_id: UUID
    checkout_url: str
    expires_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BillingStatusOut(BaseModel):
    """Overall billing status"""
    trial: TrialStatusOut
    credits_purchased: int
    last_purchase_at: Optional[datetime] = None
    recent_purchases: List[PurchaseOut] = []
    model_config = ConfigDict(from_attributes=True)


# ---------- EVENT PAYLOADS ----------
class TrialStartedPayload(BaseModel):
    """Trial started event payload"""
    merchant_id: UUID
    ends_at: datetime
    credits: int = 500


class TrialExpiredPayload(BaseModel):
    """Trial expired event payload"""
    merchant_id: UUID
    expired_at: datetime


class CreditsPurchasedPayload(BaseModel):
    """Credits purchased event payload"""
    merchant_id: UUID
    purchase_id: UUID
    credits: int
    amount: str
    platform: str


class MerchantCreatedPayload(BaseModel):
    """Merchant created event payload (consumed)"""
    merchant_id: UUID
    platform_name: str
    platform_id: str
    platform_domain: str
    name: str
    email: str
    installed_at: datetime


class PurchaseWebhookPayload(BaseModel):
    """Purchase webhook payload (consumed)"""
    charge_id: str
    status: str
    merchant_id: UUID


