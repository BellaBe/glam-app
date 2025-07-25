# shared/messaging/payloads/common.py

from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from enum import Enum

class ExternalSource(str, Enum):
    SHOPIFY="shopify"
    STRIPE="stripe"

class MerchantCreatedPayload(BaseModel):
    """Merchant created event payload"""
    merchant_id: UUID
    merchant_domain: str
    business_name: str
    contact_email: EmailStr
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    
class WebhookReceivedPayload(BaseModel):
    """Webhook received - published by webhook service, consumed by others"""
    webhook_id: UUID
    merchant_id: UUID
    source: ExternalSource
    event_type: str
    payload: Dict[str, Any]
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified: bool = True