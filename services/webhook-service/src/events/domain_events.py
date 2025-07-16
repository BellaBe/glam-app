# services/webhook-service/src/events/domain_events.py
"""Domain events for webhook service."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List

from shared.events.base import EventWrapper
from shared.events.context import EventContext
from pydantic import BaseModel


# Event payload schemas
class AppUninstalledPayload(BaseModel):
    shop_id: str
    shop_domain: str
    timestamp: str


class CatalogItemPayload(BaseModel):
    shop_id: str
    item_id: str
    external_id: str


class CatalogItemUpdatedPayload(CatalogItemPayload):
    changes: List[str]


class OrderCreatedPayload(BaseModel):
    shop_id: str
    order_id: str
    total: float
    items: List[Dict[str, Any]]


class InventoryUpdatedPayload(BaseModel):
    shop_id: str
    item_id: str
    location_id: str
    available: int


# Domain Events
class AppUninstalledEvent(EventWrapper[AppUninstalledPayload]):
    """Event emitted when an app is uninstalled"""
    
    subject: str = "evt.webhook.app.uninstalled"
    
    @classmethod
    def create(
        cls,
        shop_id: str,
        shop_domain: str,
        timestamp: datetime
    ) -> "AppUninstalledEvent":
        """Create event with auto-generated context"""
        context = EventContext.create()
        return cls.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "shop_domain": shop_domain,
                "timestamp": timestamp.isoformat()
            }
        )
    
    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: Dict[str, Any]
    ) -> "AppUninstalledEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=AppUninstalledPayload(**payload),
        )


class CatalogItemCreatedEvent(EventWrapper[CatalogItemPayload]):
    """Event emitted when a catalog item is created"""
    
    subject: str = "evt.webhook.catalog.item_created"
    
    @classmethod
    def create(
        cls,
        shop_id: str,
        item_id: str,
        external_id: str
    ) -> "CatalogItemCreatedEvent":
        """Create event with auto-generated context"""
        context = EventContext.create()
        return cls.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "item_id": item_id,
                "external_id": external_id
            }
        )
    
    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: Dict[str, Any]
    ) -> "CatalogItemCreatedEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=CatalogItemPayload(**payload),
        )


class CatalogItemUpdatedEvent(EventWrapper[CatalogItemUpdatedPayload]):
    """Event emitted when a catalog item is updated"""
    
    subject: str = "evt.webhook.catalog.item_updated"
    
    @classmethod
    def create(
        cls,
        shop_id: str,
        item_id: str,
        external_id: str,
        changes: List[str]
    ) -> "CatalogItemUpdatedEvent":
        """Create event with auto-generated context"""
        context = EventContext.create()
        return cls.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "item_id": item_id,
                "external_id": external_id,
                "changes": changes
            }
        )
    
    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: Dict[str, Any]
    ) -> "CatalogItemUpdatedEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=CatalogItemUpdatedPayload(**payload),
        )


class CatalogItemDeletedEvent(EventWrapper[CatalogItemPayload]):
    """Event emitted when a catalog item is deleted"""
    
    subject: str = "evt.webhook.catalog.item_deleted"
    
    @classmethod
    def create(
        cls,
        shop_id: str,
        item_id: str,
        external_id: str
    ) -> "CatalogItemDeletedEvent":
        """Create event with auto-generated context"""
        context = EventContext.create()
        return cls.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "item_id": item_id,
                "external_id": external_id
            }
        )
    
    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: Dict[str, Any]
    ) -> "CatalogItemDeletedEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=CatalogItemPayload(**payload),
        )


class OrderCreatedEvent(EventWrapper[OrderCreatedPayload]):
    """Event emitted when an order is created"""
    
    subject: str = "evt.webhook.order.created"
    
    @classmethod
    def create(
        cls,
        shop_id: str,
        order_id: str,
        total: float,
        items: List[Dict[str, Any]]
    ) -> "OrderCreatedEvent":
        """Create event with auto-generated context"""
        context = EventContext.create()
        return cls.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "order_id": order_id,
                "total": total,
                "items": items
            }
        )
    
    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: Dict[str, Any]
    ) -> "OrderCreatedEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=OrderCreatedPayload(**payload),
        )


class InventoryUpdatedEvent(EventWrapper[InventoryUpdatedPayload]):
    """Event emitted when inventory is updated"""
    
    subject: str = "evt.webhook.inventory.updated"
    
    @classmethod
    def create(
        cls,
        shop_id: str,
        item_id: str,
        location_id: str,
        available: int
    ) -> "InventoryUpdatedEvent":
        """Create event with auto-generated context"""
        context = EventContext.create()
        return cls.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "item_id": item_id,
                "location_id": location_id,
                "available": available
            }
        )
    
    @classmethod
    def create_from_context(
        cls, context: EventContext, payload: Dict[str, Any]
    ) -> "InventoryUpdatedEvent":
        """Create event with context"""
        return cls(
            subject=cls.subject,
            idempotency_key=context.idempotency_key,
            event_id=context.event_id,
            correlation_id=context.correlation_id,
            timestamp=context.timestamp,
            metadata=context.metadata,
            data=InventoryUpdatedPayload(**payload),
        )
