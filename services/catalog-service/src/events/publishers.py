# src/events/publishers.py
from shared.events import DomainEventPublisher, Streams
from typing import Dict, Any, List
from uuid import UUID

class CatalogEventPublisher(DomainEventPublisher):
    """Catalog domain event publisher"""
    domain_stream = Streams.CATALOG
    service_name_override = "catalog-service"
    
    async def publish_sync_fetch_requested(
        self,
        sync_id: UUID,
        shop_id: str,
        sync_type: str,
        options: Dict[str, Any],
        correlation_id: str
    ) -> str:
        """Publish sync fetch request"""
        payload = {
            "sync_id": str(sync_id),
            "shop_id": shop_id,
            "sync_type": sync_type,
            "options": options
        }
        
        return await self.publish_event(
            event_type="sync.fetch.requested.v1",
            payload=payload,
            correlation_id=correlation_id
        )
    
    async def publish_analysis_request(
        self,
        sync_id: UUID,
        shop_id: str,
        batch_id: str,
        items: List[Dict[str, Any]],
        correlation_id: str
    ) -> str:
        """Publish analysis request"""
        payload = {
            "sync_id": str(sync_id),
            "shop_id": shop_id,
            "batch_id": batch_id,
            "items": items
        }
        
        return await self.publish_event(
            event_type="analysis.request.v1",
            payload=payload,
            correlation_id=correlation_id
        )
