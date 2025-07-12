# shared/events/webhook/types.py
"""Webhook service event type definitions."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class WebhookEvents:
    """Webhook service event types"""

    # Raw webhook events
    WEBHOOK_RECEIVED = "evt.webhook.received"
    WEBHOOK_PROCESSED = "evt.webhook.processed"
    WEBHOOK_FAILED = "evt.webhook.failed"
    VALIDATION_FAILED = "evt.webhook.validation.failed"

    # Domain events (mapped from webhooks)
    # App lifecycle
    APP_UNINSTALLED = "evt.webhook.app.uninstalled"
    APP_SUBSCRIPTION_UPDATED = "evt.webhook.app.subscription_updated"
    APP_PURCHASE_UPDATED = "evt.webhook.app.purchase_updated"

    # Catalog
    CATALOG_ITEM_CREATED = "evt.webhook.catalog.item_created"
    CATALOG_ITEM_UPDATED = "evt.webhook.catalog.item_updated"
    CATALOG_ITEM_DELETED = "evt.webhook.catalog.item_deleted"

    # Orders
    ORDER_CREATED = "evt.webhook.order.created"
    ORDER_UPDATED = "evt.webhook.order.updated"
    ORDER_FULFILLED = "evt.webhook.order.fulfilled"
    ORDER_CANCELLED = "evt.webhook.order.cancelled"

    # Inventory
    INVENTORY_UPDATED = "evt.webhook.inventory.updated"
    INVENTORY_ITEM_UPDATED = "evt.webhook.inventory.item_updated"

    # Payment (Stripe)
    PAYMENT_SUCCEEDED = "evt.webhook.payment.succeeded"
    PAYMENT_FAILED = "evt.webhook.payment.failed"

    # Subscription (Stripe)
    SUBSCRIPTION_CREATED = "evt.webhook.subscription.created"
    SUBSCRIPTION_UPDATED = "evt.webhook.subscription.updated"
    SUBSCRIPTION_CANCELLED = "evt.webhook.subscription.cancelled"

    # Customer (Stripe)
    CUSTOMER_CREATED = "evt.webhook.customer.created"
    CUSTOMER_UPDATED = "evt.webhook.customer.updated"


# Event Payloads
class WebhookReceivedPayload(BaseModel):
    """Payload for webhook received event"""

    source: str
    topic: str
    merchant_id: Optional[str] = None
    merchant_domain: Optional[str] = None
    webhook_id: Optional[str] = None
    received_at: datetime


class WebhookProcessedPayload(BaseModel):
    """Payload for webhook processed event"""

    entry_id: str
    source: str
    topic: str
    event_type: str
    merchant_id: Optional[str] = None
    merchant_domain: Optional[str] = None
    processed_at: datetime


class WebhookFailedPayload(BaseModel):
    """Payload for webhook failed event"""

    entry_id: str
    source: str
    topic: str
    error: str
    attempts: int
    failed_at: datetime


class ValidationFailedPayload(BaseModel):
    """Payload for validation failed event"""

    source: str
    reason: str
    topic: Optional[str] = None
    failed_at: datetime


# Domain Event Payloads
class AppUninstalledPayload(BaseModel):
    """App uninstalled event payload"""

    merchant_id: str
    merchant_domain: str
    timestamp: datetime


class CatalogItemPayload(BaseModel):
    """Catalog item event payload"""

    merchant_id: str
    merchant_domain: Optional[str] = None
    item_id: str
    external_id: str
    title: Optional[str] = None
    changes: Optional[List[str]] = None


class OrderPayload(BaseModel):
    """Order event payload"""

    merchant_id: str
    merchant_domain: Optional[str] = None
    order_id: str
    order_number: Optional[str] = None
    total: Optional[str] = None
    currency: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
