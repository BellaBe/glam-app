# shared/shared/messaging/events/webhook.py
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WebhookAppUninstalled(BaseModel):
    """
    Payload of evt.webhook.app.uninstalled.v1 (published by webhook microservice).
    Used to locate merchant and mark UNINSTALLED.
    """

    platform_name: str = Field(..., description="e.g., shopify")
    platform_shop_id: str = Field(..., description="Shop GID or platform ID")
    domain: str | None = Field(None, description="Optional platform domain")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="Event occurrence time")


class WebhookPurchaseUpdated(BaseModel):
    """
    Payload of evt.webhook.purchase_updated.v1 (published by webhook microservice).
    Used to update purchase records.
    """

    platform_name: str = Field(..., description="e.g., shopify")
    platform_shop_id: str = Field(..., description="Shop GID or platform ID")
    domain: str = Field(..., description="Platform domain")
    purchase_id: str = Field(..., description="Platform-specific purchase ID")
    status: str = Field(..., description="Purchase status, e.g., 'COMPLETED', 'REFUNDED'")
    amount: float = Field(..., description="Purchase amount")
    currency: str = Field(..., description="Currency code, e.g., 'USD'")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="Event occurrence time")
