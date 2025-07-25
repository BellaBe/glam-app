# src/events/publishers.py
from shared.events import DomainEventPublisher, Streams
from typing import Dict, Any
from uuid import UUID
from ..schemas.product import ProductsBatchOut


class ConnectorEventPublisher(DomainEventPublisher):
    """Connector domain event publisher"""

    domain_stream = Streams.CATALOG  # Publish to catalog stream
    service_name_override = "platform-connector"

    async def publish_products_fetched(
        self, batch: ProductsBatchOut, correlation_id: str
    ) -> str:
        """Publish products fetched batch"""
        payload = batch.model_dump(mode="json")

        return await self.publish_event(
            subject="sync.products.fetched.v1",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def publish_fetch_failed(
        self, sync_id: UUID, shop_id: str, error_message: str, correlation_id: str
    ) -> str:
        """Publish fetch failure"""
        payload = {
            "sync_id": str(sync_id),
            "shop_id": shop_id,
            "error_message": error_message,
        }

        return await self.publish_event(
            subject="sync.fetch.failed.v1",
            payload=payload,
            correlation_id=correlation_id,
        )
