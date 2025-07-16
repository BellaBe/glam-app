# services/webhook-service/src/events/publishers.py
"""Event publishers for webhook service."""

from __future__ import annotations

from typing import Any

from shared.events.base_publisher import DomainEventPublisher
from shared.events.context import EventContext

from .domain_events import (
    AppUninstalledEvent,
    CatalogItemCreatedEvent, 
    CatalogItemUpdatedEvent,
    CatalogItemDeletedEvent,
    OrderCreatedEvent,
    InventoryUpdatedEvent
)


class WebhookEventPublisher(DomainEventPublisher):
    """Publisher for webhook domain events."""
    
    async def publish_app_uninstalled(
        self,
        context: EventContext,
        shop_id: str,
        shop_domain: str
    ) -> None:
        """Publish app uninstalled event."""
        
        event = AppUninstalledEvent.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "shop_domain": shop_domain,
                "timestamp": context.timestamp.isoformat()
            }
        )
        
        await self.publish_event(event)
    
    async def publish_catalog_item_created(
        self,
        context: EventContext,
        shop_id: str,
        item_id: str,
        external_id: str
    ) -> None:
        """Publish catalog item created event."""
        
        event = CatalogItemCreatedEvent.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "item_id": item_id,
                "external_id": external_id
            }
        )
        
        await self.publish_event(event)
    
    async def publish_catalog_item_updated(
        self,
        context: EventContext,
        shop_id: str,
        item_id: str,
        external_id: str,
        changes: list
    ) -> None:
        """Publish catalog item updated event."""
        
        event = CatalogItemUpdatedEvent.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "item_id": item_id,
                "external_id": external_id,
                "changes": changes
            }
        )
        
        await self.publish_event(event)
    
    async def publish_catalog_item_deleted(
        self,
        context: EventContext,
        shop_id: str,
        item_id: str,
        external_id: str
    ) -> None:
        """Publish catalog item deleted event."""
        
        event = CatalogItemDeletedEvent.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "item_id": item_id,
                "external_id": external_id
            }
        )
        
        await self.publish_event(event)
    
    async def publish_order_created(
        self,
        context: EventContext,
        shop_id: str,
        order_id: str,
        total: float,
        items: list
    ) -> None:
        """Publish order created event."""
        
        event = OrderCreatedEvent.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "order_id": order_id,
                "total": total,
                "items": items
            }
        )
        
        await self.publish_event(event)
    
    async def publish_inventory_updated(
        self,
        context: EventContext,
        shop_id: str,
        item_id: str,
        location_id: str,
        available: int
    ) -> None:
        """Publish inventory updated event."""
        
        event = InventoryUpdatedEvent.create_from_context(
            context=context,
            payload={
                "shop_id": shop_id,
                "item_id": item_id,
                "location_id": location_id,
                "available": available
            }
        )
        
        await self.publish_event(event)
