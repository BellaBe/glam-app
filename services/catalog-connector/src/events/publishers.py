# services/platform-connector/src/events/publishers.py
from shared.messaging import Publisher
from typing import Dict, Any

class PlatformEventPublisher(Publisher):
    """Publish platform connector events"""
    
    @property
    def service_name(self) -> str:
        return "platform-connector"
    
    async def platform_products_fetched(
        self,
        batch_data: Dict[str, Any],
        correlation_id: str
    ) -> str:
        """Publish products batch fetched from platform"""
        return await self.publish_event(
            subject="evt.platform.products.fetched",
            data=batch_data,
            correlation_id=correlation_id
        )
    
    async def platform_fetch_completed(
        self,
        merchant_id: str,
        sync_id: str,
        total_products: int,
        correlation_id: str
    ) -> str:
        """Publish platform fetch completed"""
        return await self.publish_event(
            subject="evt.platform.fetch.completed",
            data={
                "merchant_id": merchant_id,
                "sync_id": sync_id,
                "total_products": total_products
            },
            correlation_id=correlation_id
        )
    
    async def platform_fetch_failed(
        self,
        merchant_id: str,
        sync_id: str,
        error: str,
        correlation_id: str
    ) -> str:
        """Publish platform fetch failure"""
        return await self.publish_event(
            subject="evt.platform.fetch.failed",
            data={
                "merchant_id": merchant_id,
                "sync_id": sync_id,
                "error": error
            },
            correlation_id=correlation_id
        )