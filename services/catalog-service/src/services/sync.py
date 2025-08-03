# src/services/sync_service.py
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import redis.asyncio as redis
from shared.utils.logger import ServiceLogger
from ..repositories.sync_operation import SyncOperationRepository
from ..repositories.catalog_item import CatalogItemRepository
from ..mappers.sync_operation import SyncOperationMapper
from ..schemas.sync_operation import SyncOperationIn, SyncOperationOut
from ..models.enums import SyncOperationStatus, SyncType
from ..exceptions import SyncOperationNotFoundError, SyncOperationAlreadyRunningError
from ..events.publishers import CatalogEventPublisher
from ..config import CatalogServiceConfig

class SyncService:
    """Sync orchestration service"""
    
    def __init__(
        self,
        sync_repo: SyncOperationRepository,
        item_repo: CatalogItemRepository,
        mapper: SyncOperationMapper,
        publisher: CatalogEventPublisher,
        redis_client: redis.Redis,
        logger: ServiceLogger,
        config: CatalogServiceConfig
    ):
        self.sync_repo = sync_repo
        self.item_repo = item_repo
        self.mapper = mapper
        self.publisher = publisher
        self.redis_client = redis_client
        self.logger = logger
        self.config = config
    
    async def create_sync(
        self, 
        dto: SyncOperationIn,
        idempotency_key: str,
        correlation_id: str
    ) -> SyncOperationOut:
        """Create new sync operation with idempotency"""
        self.logger.info(f"Creating sync for shop {dto.shop_id}", extra={
            "sync_type": dto.sync_type,
            "shop_id": dto.shop_id,
            "correlation_id": correlation_id
        })
        
        # Check idempotency
        if self.config.enable_redis_idempotency:
            existing_sync_id = await self._check_idempotency(idempotency_key)
            if existing_sync_id:
                return await self.get_sync(UUID(existing_sync_id))
        
        # Check for running sync
        running_sync = await self.sync_repo.find_running_for_shop(dto.shop_id)
        if running_sync:
            raise SyncOperationAlreadyRunningError(
                f"Sync already running for shop {dto.shop_id}"
            )
        
        # Determine since timestamp for incremental sync
        since_timestamp = dto.since_timestamp
        if dto.sync_type == SyncType.INCREMENTAL and not since_timestamp:
            last_completed = await self.sync_repo.find_last_completed(dto.shop_id)
            if last_completed:
                since_timestamp = last_completed.completed_at
        
        # Create sync operation
        model = self.mapper.to_model(dto, since_timestamp=since_timestamp)
        await self.sync_repo.save(model)
        
        # Record idempotency
        if self.config.enable_redis_idempotency:
            await self._record_idempotency(idempotency_key, str(model.id))
        
        # Publish sync fetch request
        options = {
            "since_timestamp": since_timestamp.isoformat() if since_timestamp else None,
            "force_reanalysis": dto.force_reanalysis
        }
        
        await self.publisher.publish_sync_fetch_requested(
            sync_id=model.id,
            shop_id=dto.shop_id,
            sync_type=dto.sync_type,
            options=options,
            correlation_id=correlation_id
        )
        
        return self.mapper.to_out(model)
    
    async def get_sync(self, sync_id: UUID) -> SyncOperationOut:
        """Get sync operation by ID"""
        model = await self.sync_repo.find_by_id(sync_id)
        if not model:
            raise SyncOperationNotFoundError(f"Sync operation {sync_id} not found")
        return self.mapper.to_out(model)
    
    async def list_syncs(self, shop_id: str, limit: int = 10) -> List[SyncOperationOut]:
        """List sync operations for shop"""
        models = await self.sync_repo.find_by_shop_id(shop_id, limit)
        return self.mapper.list_to_out(models)
    
    async def update_sync_progress(
        self,
        sync_id: UUID,
        **updates
    ) -> SyncOperationOut:
        """Update sync operation progress"""
        model = await self.sync_repo.find_by_id(sync_id)
        if not model:
            raise SyncOperationNotFoundError(f"Sync operation {sync_id} not found")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        await self.sync_repo.save(model)
        return self.mapper.to_out(model)
    
    async def complete_sync(self, sync_id: UUID, error_message: Optional[str] = None):
        """Mark sync as completed or failed"""
        status = SyncOperationStatus.FAILED if error_message else SyncOperationStatus.COMPLETED
        
        await self.update_sync_progress(
            sync_id,
            status=status,
            completed_at=datetime.utcnow(),
            error_message=error_message
        )
        
        self.logger.info(f"Sync {sync_id} {status.lower()}", extra={
            "sync_id": str(sync_id),
            "status": status,
            "error": error_message
        })
    
    async def _check_idempotency(self, idempotency_key: str) -> Optional[str]:
        """Check if sync already exists for idempotency key"""
        redis_key = f"sync:idempotency:{idempotency_key}"
        return await self.redis_client.get(redis_key)
    
    async def _record_idempotency(self, idempotency_key: str, sync_id: str):
        """Record sync for idempotency checking"""
        redis_key = f"sync:idempotency:{idempotency_key}"
        ttl = self.config.idempotency_ttl_hours * 3600
        await self.redis_client.setex(redis_key, ttl, sync_id)
