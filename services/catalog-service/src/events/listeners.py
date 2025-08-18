# services/catalog-service/src/events/listeners.py
from typing import Any

from shared.api.correlation import set_correlation_context
from shared.messaging import Listener
from shared.utils.exceptions import ValidationError

from ..schemas.events import AnalysisCompletedPayload, ProductsFetchedPayload


class ProductsFetchedListener(Listener):
    """Listen for products fetched from platform"""

    @property
    def subject(self) -> str:
        return "evt.platform.products.fetched"

    @property
    def queue_group(self) -> str:
        return "catalog-products-handler"

    @property
    def service_name(self) -> str:
        return "catalog-service"

    def __init__(self, js_client, publisher, service, logger):
        super().__init__(js_client, logger)
        self.publisher = publisher
        self.service = service

    async def on_message(self, data: dict[str, Any]) -> None:
        """Process products batch from platform"""
        try:
            # Validate payload
            payload = ProductsFetchedPayload(**data)

            # Set correlation context from event
            if correlation_id := data.get("correlation_id"):
                set_correlation_context(correlation_id)

            # Process batch
            items, items_to_analyze = await self.service.process_product_batch(
                sync_id=payload.sync_id,
                merchant_id=payload.merchant_id,
                products=payload.products,
                batch_num=payload.batch_num,
                has_more=payload.has_more,
                correlation_id=correlation_id or "unknown",
            )

            # Request analysis if items have images
            if items_to_analyze:
                await self.publisher.catalog_analysis_requested(
                    merchant_id=payload.merchant_id,
                    sync_id=payload.sync_id,
                    items=items_to_analyze,
                    correlation_id=correlation_id or "unknown",
                )

            # If no more batches, complete sync
            if not payload.has_more:
                await self.service.complete_sync(
                    sync_id=payload.sync_id,
                    status="completed",
                    correlation_id=correlation_id or "unknown",
                )

                # Publish completion event
                await self.publisher.catalog_sync_completed(
                    merchant_id=payload.merchant_id,
                    sync_id=payload.sync_id,
                    total_items=len(items),
                    duration_seconds=0,  # Calculate from start time
                    correlation_id=correlation_id or "unknown",
                )

        except ValidationError as e:
            self.logger.error(f"Invalid products batch: {e}")
            # ACK to prevent retry of invalid messages
            return
        except Exception as e:
            self.logger.error(f"Products processing failed: {e}", exc_info=True)
            raise  # NACK for retry


class AnalysisCompletedListener(Listener):
    """Listen for AI analysis results"""

    @property
    def subject(self) -> str:
        return "evt.analysis.completed"

    @property
    def queue_group(self) -> str:
        return "catalog-analysis-handler"

    @property
    def service_name(self) -> str:
        return "catalog-service"

    def __init__(self, js_client, analysis_repo, catalog_repo, logger):
        super().__init__(js_client, logger)
        self.analysis_repo = analysis_repo
        self.catalog_repo = catalog_repo

    async def on_message(self, data: dict[str, Any]) -> None:
        """Store AI analysis results"""
        try:
            # Validate payload
            payload = AnalysisCompletedPayload(**data)

            # Store analysis result
            await self.analysis_repo.create(
                {
                    "item_id": payload.item_id,
                    "model_version": payload.model_version,
                    "category": payload.category,
                    "subcategory": payload.subcategory,
                    "description": payload.description,
                    "gender": payload.gender,
                    "attributes": payload.attributes,
                    "quality_score": payload.quality_score,
                    "confidence_score": payload.confidence_score,
                    "processing_time_ms": payload.processing_time_ms,
                }
            )

            # Update catalog item status
            await self.catalog_repo.update_analysis_status(item_id=payload.item_id, status="analyzed")

            self.logger.info(
                f"Stored analysis for item {payload.item_id}",
                extra={"item_id": payload.item_id},
            )

        except ValidationError as e:
            self.logger.error(f"Invalid analysis result: {e}")
            return  # ACK invalid messages
        except Exception as e:
            self.logger.error(f"Analysis storage failed: {e}", exc_info=True)
            raise  # NACK for retry
