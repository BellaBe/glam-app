# services/catalog-service/src/services/catalog_service.py
import json
from datetime import datetime

import redis.asyncio as redis

from shared.utils.exceptions import ConflictError, NotFoundError
from shared.utils.logger import ServiceLogger

from ..repositories.catalog_repository import CatalogRepository
from ..repositories.sync_repository import SyncRepository
from ..schemas.catalog import CatalogItemCreate, CatalogItemOut
from ..schemas.sync import SyncOperationCreate, SyncOperationOut, SyncProgressOut


class CatalogService:
    """Catalog business logic - orchestrates sync and storage"""

    def __init__(
        self,
        catalog_repo: CatalogRepository,
        sync_repo: SyncRepository,
        redis_client: redis.Redis | None,
        logger: ServiceLogger,
        config: dict,
    ):
        self.catalog_repo = catalog_repo
        self.sync_repo = sync_repo
        self.redis = redis_client
        self.logger = logger
        self.config = config

    async def start_sync(
        self,
        merchant_id: str,
        platform_name: str,
        platform_id: str,
        platform_domain: str,
        sync_type: str,
        correlation_id: str,
    ) -> SyncOperationOut:
        """Start catalog sync operation"""

        # Check for existing running sync
        existing = await self.sync_repo.find_running_for_merchant(merchant_id)
        if existing:
            raise ConflictError(
                message="Sync already in progress",
                conflicting_resource="sync_operation",
                current_state=existing.status,
                details={"sync_id": existing.id},
            )

        # Create sync operation
        sync_dto = SyncOperationCreate(
            merchant_id=merchant_id,
            platform_name=platform_name,
            platform_id=platform_id,
            platform_domain=platform_domain,
            sync_type=sync_type,
        )

        sync = await self.sync_repo.create(sync_dto)

        # Cache initial progress for polling
        if self.redis:
            await self._cache_progress(
                sync.id,
                status="pending",
                progress_percent=0,
                message="Initializing sync...",
                total_products=0,
                processed_products=0,
            )

        self.logger.info(
            "Started catalog sync",
            extra={
                "correlation_id": correlation_id,
                "sync_id": sync.id,
                "merchant_id": merchant_id,
                "platform": platform_name,
            },
        )

        return sync

    async def get_sync_progress(self, sync_id: str, correlation_id: str) -> SyncProgressOut:
        """Get sync progress for polling"""

        # Try cache first
        if self.redis:
            cached = await self._get_cached_progress(sync_id)
            if cached:
                return cached

        # Fallback to database
        sync = await self.sync_repo.find_by_id(sync_id)
        if not sync:
            raise NotFoundError(
                message=f"Sync operation {sync_id} not found",
                resource="sync_operation",
                resource_id=sync_id,
            )

        return SyncProgressOut(
            sync_id=sync.id,
            status=sync.status,
            progress_percent=sync.progress_percent,
            message=sync.progress_message or "",
            total_products=sync.total_products,
            processed_products=sync.processed_products,
            failed_products=sync.failed_products,
            started_at=sync.started_at,
            completed_at=sync.completed_at,
        )

    async def process_product_batch(
        self,
        sync_id: str,
        merchant_id: str,
        products: list[dict],
        batch_num: int,
        has_more: bool,
        correlation_id: str,
    ) -> list[CatalogItemOut]:
        """Process batch of products from platform"""

        items_created = []
        items_to_analyze = []

        for product in products:
            # Create DTO
            item_dto = CatalogItemCreate(
                merchant_id=merchant_id,
                platform_name=product.get("platform_name", "shopify"),
                platform_id=product["platform_id"],
                platform_domain=product["platform_domain"],
                product_id=product["product_id"],
                variant_id=product["variant_id"],
                image_id=product.get("image_id"),
                product_title=product["product_title"],
                variant_title=product.get("variant_title", ""),
                sku=product.get("sku"),
                price=product["price"],
                currency=product.get("currency", "USD"),
                inventory_quantity=product.get("inventory", 0),
                image_url=product.get("image_url"),
                platform_created_at=product.get("created_at"),
                platform_updated_at=product.get("updated_at"),
                synced_at=datetime.utcnow(),
            )

            # Upsert catalog item
            item = await self.catalog_repo.upsert(item_dto)
            items_created.append(item)

            # Queue for analysis if has image
            if item.image_url:
                items_to_analyze.append({"item_id": item.id, "image_url": item.image_url})

        # Update progress
        sync = await self.sync_repo.find_by_id(sync_id)
        if sync:
            processed = sync.processed_products + len(products)
            progress_percent = min(90, int((processed / max(sync.total_products, 1)) * 90))

            await self.sync_repo.update_progress(
                sync_id=sync_id,
                processed=processed,
                failed=sync.failed_products,
                progress_percent=progress_percent,
                message=f"Processed batch {batch_num}, {processed} products synced",
            )

            # Update cache
            if self.redis:
                await self._cache_progress(
                    sync_id=sync_id,
                    status="running",
                    progress_percent=progress_percent,
                    message=f"Processing batch {batch_num}...",
                    total_products=sync.total_products,
                    processed_products=processed,
                )

        self.logger.info(
            f"Processed product batch {batch_num}",
            extra={
                "correlation_id": correlation_id,
                "sync_id": sync_id,
                "batch_size": len(products),
                "items_to_analyze": len(items_to_analyze),
            },
        )

        return items_created, items_to_analyze

    async def get_catalog_status(self, merchant_id: str, correlation_id: str) -> dict:
        """Get catalog status for merchant"""

        # Get product count
        product_count = await self.catalog_repo.count_by_merchant(merchant_id)

        # Get last sync
        last_sync = await self.sync_repo.find_by_id(merchant_id)  # Would need a proper query

        return {
            "product_count": product_count,
            "last_sync_at": last_sync.completed_at if last_sync else None,
            "sync_status": last_sync.status if last_sync else "never_synced",
        }

    async def _cache_progress(
        self,
        sync_id: str,
        status: str,
        progress_percent: int,
        message: str,
        total_products: int,
        processed_products: int,
    ) -> None:
        """Cache progress in Redis for fast polling"""
        if not self.redis:
            return

        data = {
            "status": status,
            "progress_percent": progress_percent,
            "message": message,
            "total_products": total_products,
            "processed_products": processed_products,
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self.redis.setex(
            f"sync:{sync_id}",
            self.config.get("sync_progress_ttl", 3600),
            json.dumps(data),
        )

    async def _get_cached_progress(self, sync_id: str) -> SyncProgressOut | None:
        """Get cached progress from Redis"""
        if not self.redis:
            return None

        data = await self.redis.get(f"sync:{sync_id}")
        if not data:
            return None

        progress = json.loads(data)
        return SyncProgressOut(
            sync_id=sync_id,
            status=progress["status"],
            progress_percent=progress["progress_percent"],
            message=progress["message"],
            total_products=progress["total_products"],
            processed_products=progress["processed_products"],
            failed_products=0,
            started_at=None,
            completed_at=None,
        )
