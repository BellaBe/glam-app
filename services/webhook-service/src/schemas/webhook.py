from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any


# ---------- INPUT DTOs ----------
class WebhookHeaders(BaseModel):
    """Webhook headers from Shopify"""
    hmac_sha256: str = Field(..., alias="X-Shopify-Hmac-Sha256")
    topic: str = Field(..., alias="X-Shopify-Topic")
    shop_domain: str = Field(..., alias="X-Shopify-Shop-Domain")
    webhook_id: str = Field(..., alias="X-Shopify-Webhook-Id")
    api_version: Optional[str] = Field(None, alias="X-Shopify-Api-Version")
    
    model_config = ConfigDict(populate_by_name=True)


# ---------- OUTPUT DTOs ----------
class WebhookResponse(BaseModel):
    """Standard webhook response"""
    success: bool
    webhook_id: str


class WebhookEntryOut(BaseModel):
    """Output DTO for webhook entry"""
    id: UUID
    platform: str
    topic_raw: str
    topic_enum: str
    shop_domain: str
    webhook_id: str
    api_version: Optional[str]
    status: str
    processing_attempts: int
    error_message: Optional[str]
    received_at: datetime
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ---------- INTERNAL DTOs ----------
class WebhookProcessMessage(BaseModel):
    """Message for async webhook processing"""
    webhook_id: str
    request_id: str
    correlation_id: str


