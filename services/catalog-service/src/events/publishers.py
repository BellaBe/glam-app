from shared.messaging.publisher import Publisher
from ..schemas.catalog_sync import (
    SyncRequestedPayload,
    AnalysisRequestedPayload,
    SyncStartedPayload,
    SyncProgressPayload,
    SyncCompletedPayload
)

class CatalogEventPublisher(Publisher):
    @property
    def service_name(self) -> str:
        return "catalog-service"
    
    async def sync_requested(self, payload: SyncRequestedPayload) -> str:
        """Publish catalog sync requested event"""
        return await self.publish_event(
            subject="evt.catalog.sync.requested",
            data=payload.model_dump(),
        )
    
    async def analysis_requested(self, payload: AnalysisRequestedPayload) -> str:
        """Publish analysis requested event"""
        return await self.publish_event(
            subject="evt.catalog.analysis.requested",
            data=payload.model_dump(),
        )
    
    async def sync_started(self, payload: SyncStartedPayload) -> str:
        """Publish sync started event"""
        return await self.publish_event(
            subject="evt.catalog.sync.started",
            data=payload.model_dump(),
        )
    
    async def sync_progress(self, payload: SyncProgressPayload) -> str:
        """Publish sync progress event"""
        return await self.publish_event(
            subject="evt.catalog.sync.progress",
            data=payload.model_dump(),
        )
    
    async def sync_completed(self, payload: SyncCompletedPayload) -> str:
        """Publish sync completed event"""
        return await self.publish_event(
            subject="evt.catalog.sync.completed",
            data=payload.model_dump(),
        )

# ================================================================
