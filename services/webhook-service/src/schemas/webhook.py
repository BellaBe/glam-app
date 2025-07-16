# services/webhook-service/src/schemas/webhook.py
"""Webhook-related request/response schemas"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from ..models.webhook_entry import WebhookStatus


class CreateWebhookSchema(BaseModel):
    id: UUID = Field(default_factory=UUID, description="Unique identifier for the webhook entry")
    platform: str = Field(..., description="Platform for which the webhook is created")
    topic: str = Field(..., description="Webhook topic (e.g., 'orders/create')")
    shop_id: str = Field(..., description="Shop identifier where the webhook is registered")
    status: WebhookStatus = Field(..., description="Current status of the webhook entry")
    attempts: int = Field(0, description="Number of processing attempts")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    received_at: datetime = Field(default_factory=datetime.utcnow, description="When the webhook was received")
    processed_at: Optional[datetime] = Field(None, description="When the webhook was processed")

class ShopifyWebhookHeaders(BaseModel):
    """Expected headers for Shopify webhooks"""
    
    x_shopify_topic: str = Field(..., alias="X-Shopify-Topic")
    x_shopify_hmac_sha256: str = Field(..., alias="X-Shopify-Hmac-Sha256")
    x_shopify_shop_domain: str = Field(..., alias="X-Shopify-Shop-Domain")
    x_shopify_api_version: str = Field(..., alias="X-Shopify-API-Version")
    x_shopify_webhook_id: str = Field(..., alias="X-Shopify-Webhook-Id")


class WebhookRequest(BaseModel):
    """Generic webhook request body"""
    
    data: Dict[str, Any] = Field(..., description="Webhook payload data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": 12345,
                    "shop_domain": "example-shop.myshopify.com",
                    "created_at": "2025-01-15T10:00:00Z"
                }
            }
        }


class WebhookResponse(BaseModel):
    """Webhook processing response"""
    
    success: bool = Field(..., description="Whether webhook was processed successfully")
    webhook_id: UUID = Field(..., description="Internal webhook entry ID")
    message: str = Field(..., description="Processing result message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "webhook_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Webhook processed successfully"
            }
        }


class WebhookEntryResponse(BaseModel):
    """Webhook entry response schema"""
    
    id: UUID
    platform: str
    topic: str
    shop_id: str
    status: WebhookStatus
    attempts: int
    error: Optional[str] = None
    received_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """Paginated list of webhook entries"""
    
    webhooks: List[WebhookEntryResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool
