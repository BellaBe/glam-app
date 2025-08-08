import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from shared.utils.logger import ServiceLogger
from shared.api.correlation import get_correlation_context
from ..config import ServiceConfig
from ..repositories.catalog_state_repository import CatalogStateRepository
from ..repositories.sync_job_repository import SyncJobRepository
from ..repositories.sync_item_repository import SyncItemRepository
from ..events.publishers import CatalogEventPublisher
from ..schemas.catalog_sync import (
    SyncAllowedOut,
    SyncStatusOut,
    SyncRequestedPayload,
    AnalysisRequestedPayload,
    SyncStartedPayload,
    SyncProgressPayload,
    SyncCompletedPayload
)
from ..exceptions import (
    SyncNotAllowedError,
    SyncAlreadyActiveError,
    SyncNotFoundError,
    InvalidSyncTypeError
)
from .cache_service import CacheService

class CatalogSyncService:
    """Service for managing catalog synchronization"""
    
    def __init__(
        self,
        catalog_state_repo: CatalogStateRepository,
        sync_job_repo: SyncJobRepository,
        sync_item_repo: SyncItemRepository,
        event_publisher: CatalogEventPublisher,
        cache_service: CacheService,
        logger: ServiceLogger,
        config: ServiceConfig
    ):
        self.catalog_state_repo = catalog_state_repo
        self.sync_job_repo = sync_job_repo
        self.sync_item_repo = sync_item_repo
        self.event_publisher = event_publisher
        self.cache_service = cache_service
        self.logger = logger
        self.config = config
        
        # Progress update throttling
        self._last_progress_update: Dict[str, datetime] = {}
        self._progress_throttle_seconds = 5
    
    async def check_sync_allowed(self, shop_domain: str) -> SyncAllowedOut:
        """Check if sync is allowed for merchant"""
        # Check cached state first
        allowed, reason = await self.cache_service.get_sync_allowed_state(shop_domain)
        if not allowed:
            return SyncAllowedOut(allowed=False, reason=reason)
        
        # Check for active sync
        state = await self.catalog_state_repo.find_by_shop_domain(shop_domain)
        if state and state.activeSyncId:
            return SyncAllowedOut(allowed=False, reason="sync_active")
        
        return SyncAllowedOut(allowed=True, reason="ok")
    
    async def start_sync(self, shop_domain: str, sync_type: str = "full") -> str:
        """Start a new sync job"""
        if sync_type != "full":
            raise InvalidSyncTypeError("Only 'full' sync type is supported")
        
        # Verify allowed
        allowed = await self.check_sync_allowed(shop_domain)
        if not allowed.allowed:
            raise SyncNotAllowedError(f"Sync not allowed: {allowed.reason}")
        
        # Check for active sync again (race condition)
        active_sync = await self.sync_job_repo.find_active_sync(shop_domain)
        if active_sync:
            raise SyncAlreadyActiveError(
                "Active sync already exists",
                conflicting_resource="sync",
                current_state=active_sync.id
            )
        
        # Create sync job
        sync_job = await self.sync_job_repo.create(shop_domain, sync_type)
        
        # Update catalog state
        await self.catalog_state_repo.set_active_sync(shop_domain, sync_job.id)
        
        # Publish sync started event
        await self.event_publisher.sync_started(
            SyncStartedPayload(
                shopDomain=shop_domain,
                syncId=sync_job.id,
                totalProducts=0
            )
        )
        
        # Publish sync requested event
        await self.event_publisher.sync_requested(
            SyncRequestedPayload(
                syncId=sync_job.id,
                shopDomain=shop_domain,
                type=sync_type
            )
        )
        
        # Update status to running
        await self.sync_job_repo.update_status(sync_job.id, "running")
        
        self.logger.info(
            f"Started sync for {shop_domain}",
            extra={
                "sync_id": sync_job.id,
                "shop_domain": shop_domain,
                "correlation_id": get_correlation_context()
            }
        )
        
        return sync_job.id
    
    async def get_sync_status(self, shop_domain: str) -> SyncStatusOut:
        """Get current sync status for merchant"""
        state = await self.catalog_state_repo.find_by_shop_domain(shop_domain)
        
        # Get latest sync
        latest_sync = await self.sync_job_repo.get_latest_sync(shop_domain)
        
        if not latest_sync:
            return SyncStatusOut(
                sync="queued",  # No sync yet
                analysis="idle",
                totalProducts=0,
                processedProducts=0,
                progress=0,
                lastSyncAt=None,
                hasSyncedBefore=False,
                error=None
            )
        
        # Calculate progress
        progress_data = self._calculate_progress(latest_sync)
        
        return SyncStatusOut(
            sync=latest_sync.status,
            analysis=latest_sync.analysisStatus,
            totalProducts=latest_sync.totalProducts,
            processedProducts=progress_data["processedProducts"],
            progress=progress_data["progress"],
            lastSyncAt=state.lastSyncAt if state else None,
            hasSyncedBefore=state.hasSyncedBefore if state else False,
            error=latest_sync.errorMessage
        )
    
    async def handle_catalog_item(self, event_data: dict) -> None:
        """Handle incoming catalog item from platform connector"""
        sync_id = event_data["syncId"]
        shop_domain = event_data["shopDomain"]
        
        # Validate sync exists and is active
        sync = await self.sync_job_repo.find_by_id(sync_id)
        if not sync or sync.status != "running":
            self.logger.warning(f"Ignoring item for inactive sync {sync_id}")
            return
        
        # Check for duplicate
        if await self.sync_item_repo.exists(sync_id, event_data["variantId"]):
            self.logger.debug(f"Duplicate item ignored: {event_data['variantId']}")
            return
        
        # Create sync item
        await self.sync_item_repo.create({
            "syncId": sync_id,
            "shopDomain": shop_domain,
            "productId": event_data["productId"],
            "variantId": event_data["variantId"],
            "imageUrl": event_data["imageUrl"],
            "status": "queued"
        })
        
        # Increment submitted counter
        await self.sync_job_repo.increment_submitted(sync_id)
        
        # Update analysis status if first item
        if sync.analysisStatus == "idle":
            await self.sync_job_repo.update_analysis_status(sync_id, "requested")
        
        # Publish analysis request
        await self.event_publisher.analysis_requested(
            AnalysisRequestedPayload(
                syncId=sync_id,
                shopDomain=shop_domain,
                productId=event_data["productId"],
                variantId=event_data["variantId"],
                imageUrl=event_data["imageUrl"],
                metadata={"sku": event_data.get("sku")}
            )
        )
        
        # Update item status
        await self.sync_item_repo.update_status(sync_id, event_data["variantId"], "submitted")
        
        # Maybe publish progress update
        await self._maybe_publish_progress(sync)
    
    async def handle_analysis_completed(self, event_data: dict) -> None:
        """Handle analysis completion event"""
        sync_id = event_data["syncId"]
        variant_id = event_data["variantId"]
        success = event_data["success"]
        error = event_data.get("error")
        
        # Update sync item status
        status = "completed" if success else "failed"
        await self.sync_item_repo.update_status(sync_id, variant_id, status, error)
        
        # Update counters
        sync = await self.sync_job_repo.find_by_id(sync_id)
        if not sync:
            self.logger.error(f"Sync not found for analysis completion: {sync_id}")
            return
        
        if success:
            await self.sync_job_repo.increment_completed(sync_id)
        else:
            await self.sync_job_repo.increment_failed(sync_id)
        
        # Update analysis status
        if sync.analysisStatus == "requested":
            await self.sync_job_repo.update_analysis_status(sync_id, "analyzing")
        
        # Check if all items are processed
        sync = await self.sync_job_repo.find_by_id(sync_id)  # Refetch
        total_processed = sync.completedItems + sync.failedItems
        
        if total_processed >= sync.submittedItems and sync.submittedItems > 0:
            await self._complete_sync(sync)
        else:
            await self._maybe_publish_progress(sync)
    
    async def _complete_sync(self, sync) -> None:
        """Complete the sync process"""
        # Update statuses
        await self.sync_job_repo.update_status(sync.id, "synced")
        await self.sync_job_repo.update_analysis_status(sync.id, "analyzed")
        
        # Clear active sync
        await self.catalog_state_repo.clear_active_sync(sync.shopDomain)
        
        # Calculate duration
        duration_ms = int((datetime.utcnow() - sync.startedAt).total_seconds() * 1000)
        
        # Publish completion event
        await self.event_publisher.sync_completed(
            SyncCompletedPayload(
                shopDomain=sync.shopDomain,
                syncId=sync.id,
                submitted=sync.submittedItems,
                completed=sync.completedItems,
                failed=sync.failedItems,
                durationMs=duration_ms
            )
        )
        
        self.logger.info(
            f"Sync completed for {sync.shopDomain}",
            extra={
                "sync_id": sync.id,
                "duration_ms": duration_ms,
                "submitted": sync.submittedItems,
                "completed": sync.completedItems,
                "failed": sync.failedItems
            }
        )
    
    def _calculate_progress(self, sync) -> dict:
        """Calculate sync progress"""
        if sync.submittedItems == 0:
            return {"progress": 0, "processedProducts": 0}
        
        processed = sync.completedItems + sync.failedItems
        progress = min(int(processed / sync.submittedItems * 100), 100)
        
        # Derive processed products (approximate)
        if sync.totalVariants > 0 and sync.totalProducts > 0:
            avg_variants_per_product = sync.totalVariants / sync.totalProducts
            processed_products = min(
                int(processed / avg_variants_per_product),
                sync.totalProducts
            )
        else:
            processed_products = processed  # Fallback 1:1 ratio
        
        return {
            "progress": progress,
            "processedProducts": processed_products
        }
    
    async def _maybe_publish_progress(self, sync) -> None:
        """Publish progress update if not throttled"""
        now = datetime.utcnow()
        last_update = self._last_progress_update.get(sync.id)
        
        if last_update and (now - last_update).total_seconds() < self._progress_throttle_seconds:
            return
        
        self._last_progress_update[sync.id] = now
        
        await self.event_publisher.sync_progress(
            SyncProgressPayload(
                shopDomain=sync.shopDomain,
                syncId=sync.id,
                submitted=sync.submittedItems,
                completed=sync.completedItems,
                failed=sync.failedItems
            )
        )

# ================================================================
