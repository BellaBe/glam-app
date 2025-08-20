# services/catalog-ai-analyzer/src/events/publishers.py
from shared.messaging.publisher import Publisher
from ..schemas.events import (
    CatalogAnalysisCompletedPayload,
    CatalogBatchCompletedPayload
)

class CatalogAIPublisher(Publisher):
    """Publish catalog AI analysis events"""
    
    @property
    def service_name(self) -> str:
        return "catalog-ai-analyzer"
    
    async def analysis_completed(
        self, 
        payload: CatalogAnalysisCompletedPayload,
        correlation_id: str
    ) -> str:
        """Publish individual item analysis completed"""
        return await self.publish_event(
            subject="evt.catalog.ai.analysis.completed",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id
        )
    
    async def batch_completed(
        self,
        payload: CatalogBatchCompletedPayload,
        correlation_id: str
    ) -> str:
        """Publish batch processing completed"""
        return await self.publish_event(
            subject="evt.catalog.ai.batch.completed",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id
        )