# services/credit-service/src/schemas/events.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# Event payloads consumed
class MerchantCreatedPayload(BaseModel):
    """Merchant created event from merchant service"""

    merchant_id: UUID
    platform: str  # 'shopify', 'woocommerce', etc
    domain: str
    shop_gid: str  # Platform-specific ID


class TrialStartedPayload(BaseModel):
    """Trial started event from billing service"""

    merchant_id: UUID
    ends_at: datetime


class CreditsPurchasedPayload(BaseModel):
    """Credits purchased event from billing service"""

    merchant_id: UUID
    credits: int
    purchase_id: str


class MatchCompletedPayload(BaseModel):
    """Match completed event from recommendation service"""

    merchant_id: UUID
    match_id: str
    shopper_id: str
    matched_items_count: int


# Event payloads published
class CreditsGrantedPayload(BaseModel):
    """Credits granted event"""

    merchant_id: UUID
    amount: int
    balance: int
    reference_type: str
    reference_id: str
    platform_name: str


class CreditsConsumedPayload(BaseModel):
    """Credits consumed event"""

    merchant_id: UUID
    amount: int
    balance: int
    reference_type: str
    reference_id: str
    platform_name: str


class CreditsInsufficientPayload(BaseModel):
    """Credits insufficient event"""

    merchant_id: UUID
    attempted_amount: int
    balance: int
    platform_name: str


class CreditsLowBalancePayload(BaseModel):
    """Low balance warning event"""

    merchant_id: UUID
    balance: int
    threshold: int
    platform_name: str


class CreditsExhaustedPayload(BaseModel):
    """Credits exhausted event"""

    merchant_id: UUID
    platform_name: str
