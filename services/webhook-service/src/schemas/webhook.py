# services/webhook-service/src/schemas/webhook.py
"""Webhook schemas for API requests and responses."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ..models.webhook import WebhookStatus


class WebhookHeaders(BaseModel):
    """Common webhook headers"""

    content_type: str = Field(alias="Content-Type")
    user_agent: Optional[str] = Field(None, alias="User-Agent")

    # Platform specific headers will be in extra
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ShopifyWebhookHeaders(WebhookHeaders):
    """Shopify specific webhook headers"""

    x_shopify_topic: str = Field(alias="X-Shopify-Topic")
    x_shopify_hmac_sha256: str = Field(alias="X-Shopify-Hmac-Sha256")
    x_shopify_merchant_domain: str = Field(alias="X-Shopify-Shop-Domain")
    x_shopify_api_version: Optional[str] = Field(None, alias="X-Shopify-API-Version")
    x_shopify_webhook_id: Optional[str] = Field(None, alias="X-Shopify-Webhook-Id")


class WebhookReceive(BaseModel):
    """Schema for receiving webhook data"""

    platform: str
    topic: Optional[str] = None  # May come from headers
    headers: Dict[str, Any]
    body: Dict[str, Any]
    raw_body: bytes = Field(exclude=True)  # For signature validation

    @field_validator("platform")
    def validate_platform(cls, v):
        """Validate platform is supported"""
        supported = ["shopify", "stripe", "square"]  # Add more as needed
        if v.lower() not in supported:
            raise ValueError(f"Platform {v} not supported. Must be one of {supported}")
        return v.lower()


class WebhookCreate(BaseModel):
    """Internal schema for creating webhook record"""

    platform: str
    topic: str
    webhook_id: Optional[str] = None
    merchant_id: str
    payload: Dict[str, Any]
    headers: Dict[str, Any]
    signature: Optional[str] = None
    status: WebhookStatus = WebhookStatus.RECEIVED


class WebhookUpdate(BaseModel):
    """Update webhook status"""

    status: WebhookStatus
    error: Optional[str] = None
    processed_at: Optional[datetime] = None
    published_event_id: Optional[str] = None
    published_event_type: Optional[str] = None
    attempts: Optional[int] = None


class WebhookFilter(BaseModel):
    """Filter parameters for webhook queries"""

    platform: Optional[str] = None
    topic: Optional[str] = None
    merchant_id: Optional[str] = None
    status: Optional[WebhookStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class WebhookResponse(BaseModel):
    """Basic webhook response"""

    id: UUID
    platform: str
    topic: str
    merchant_id: str
    status: WebhookStatus
    received_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookDetailResponse(WebhookResponse):
    """Detailed webhook response with full information"""

    webhook_id: Optional[str] = None
    payload: Dict[str, Any]
    headers: Dict[str, Any]
    signature: Optional[str] = None
    attempts: int
    error: Optional[str] = None
    published_event_id: Optional[str] = None
    published_event_type: Optional[str] = None


class WebhookStats(BaseModel):
    """Webhook statistics"""

    total: int
    by_status: Dict[str, int]
    by_platform: Dict[str, int]
    by_topic: Dict[str, int]
    success_rate: float
    average_processing_time_ms: Optional[float] = None
