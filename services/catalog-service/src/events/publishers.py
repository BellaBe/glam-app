# services/catalog-service/src/events/publishers.py
from shared.messaging import Publisher
from shared.api.correlation import get_correlation_context

class CatalogEventPublisher(Publisher):
    """Publish catalog domain events"""
    
    @property
    def service_name(self) -> str:
        return "catalog-service"
    
    async def catalog_sync_requested(
        self,
        merchant_id: str,
        platform_name: str,
        platform_shop_id: str,
        shop_domain: str,
        sync_id: str,
        sync_type: str,
        correlation_id: str
    ) -> str:
        """Publish catalog sync requested event"""
        return await self.publish_event(
            subject="evt.catalog.sync.requested",
            data={
                "merchant_id": merchant_id,
                "platform_name": platform_name,
                "platform_shop_id": platform_shop_id,
                "shop_domain": shop_domain,
                "sync_id": sync_id,
                "sync_type": sync_type
            },
            correlation_id=correlation_id
        )
    
    async def catalog_analysis_requested(
        self,
        merchant_id: str,
        sync_id: str,
        items: list,
        correlation_id: str
    ) -> str:
        """Request AI analysis for catalog items"""
        return await self.publish_event(
            subject="evt.catalog.analysis.requested",
            data={
                "merchant_id": merchant_id,
                "sync_id": sync_id,
                "items": items
            },
            correlation_id=correlation_id
        )
    
    async def catalog_sync_completed(
        self,
        merchant_id: str,
        sync_id: str,
        total_items: int,
        duration_seconds: float,
        correlation_id: str
    ) -> str:
        """Publish sync completed event"""
        return await self.publish_event(
            subject="evt.catalog.sync.completed",
            data={
                "merchant_id": merchant_id,
                "sync_id": sync_id,
                "total_items": total_items,
                "duration_seconds": duration_seconds
            },
            correlation_id=correlation_id
        )