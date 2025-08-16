================
# services/catalog-analysis/src/events/publishers.py
================
from shared.events import DomainEventPublisher, Streams


class CatalogAnalysisEventPublisher(DomainEventPublisher):
    """Catalog analysis specific event publisher"""

    domain_stream = Streams.CATALOG
    service_name_override = "catalog-analysis"


================
# services/catalog-analysis/src/events/subscribers.py
================
from shared.events import DomainEventSubscriber
from ..services.catalog_analysis_service import CatalogAnalysisService
from ..schemas.catalog_item import CatalogItemAnalysisRequest
from .types import CatalogAnalysisEvents


class CatalogItemAnalysisSubscriber(DomainEventSubscriber):
    """Subscribe to catalog item analysis requests"""

    stream_name = "CATALOG"
    subject = CatalogAnalysisEvents.ITEM_ANALYSIS_REQUESTED
    subject = CatalogAnalysisEvents.ITEM_ANALYSIS_REQUESTED
    durable_name = "catalog-analysis-requests"

    async def on_event(self, event: dict, headers: dict):
        """Process catalog item analysis request"""
        # Get injected dependencies
        service = self.get_dependency("catalog_analysis_service")
        publisher = self.get_dependency("publisher")
        logger = self.get_dependency("logger")

        payload = event["payload"]
        correlation_id = event.get("correlation_id")

        logger.info(
            "Processing catalog item analysis request",
            extra={
                "subject": self.subject,
                "correlation_id": correlation_id,
                "shop_id": payload.get("shop_id"),
                "product_id": payload.get("product_id"),
                "variant_id": payload.get("variant_id"),
            },
        )

        try:
            # Parse request
            request = CatalogItemAnalysisRequest(**payload)

            # Process catalog item analysis
            result = await service.analyze_catalog_item(request)

            # Publish result event based on status
            if result.status == "success":
                await publisher.publish_event(
                    subject=CatalogAnalysisEvents.ITEM_ANALYSIS_COMPLETED,
                    payload=result.model_dump(),
                    correlation_id=correlation_id,
                )
            else:
                await publisher.publish_event(
                    subject=CatalogAnalysisEvents.ITEM_ANALYSIS_FAILED,
                    payload=result.model_dump(),
                    correlation_id=correlation_id,
                )

        except Exception as e:
            logger.error(
                f"Failed to process catalog item analysis request: {str(e)}", exc_info=True
            )

            # Publish failure event
            await publisher.publish_event(
                subject=CatalogAnalysisEvents.ITEM_ANALYSIS_FAILED,
                payload={
                    "status": "error",
                    "error": str(e),
                    "shop_id": payload.get("shop_id"),
                    "product_id": payload.get("product_id"),
                    "variant_id": payload.get("variant_id"),
                    "latency_ms": 0,
                    "colours": None,
                },
                correlation_id=correlation_id,
            )
