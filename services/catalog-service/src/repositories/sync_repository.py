# services/catalog-service/src/repositories/sync_repository.py
from datetime import datetime

from prisma import Prisma  # type: ignore[attr-defined]

from ..schemas.sync import SyncOperationCreate, SyncOperationOut


class SyncRepository:
    """Repository for sync operations"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def create(self, dto: SyncOperationCreate) -> SyncOperationOut:
        """Create sync operation"""
        sync = await self.prisma.syncoperation.create(
            data={
                "merchant_id": dto.merchant_id,
                "platform_name": dto.platform_name,
                "platform_id": dto.platform_id,
                "platform_domain": dto.platform_domain,
                "sync_type": dto.sync_type,
                "status": "pending",
            }
        )
        return SyncOperationOut.model_validate(sync)

    async def find_by_id(self, sync_id: str) -> SyncOperationOut | None:
        """Find sync operation by ID"""
        sync = await self.prisma.syncoperation.find_unique(where={"id": sync_id})
        return SyncOperationOut.model_validate(sync) if sync else None

    async def find_running_for_merchant(self, merchant_id: str) -> SyncOperationOut | None:
        """Find running sync for merchant"""
        sync = await self.prisma.syncoperation.find_first(
            where={"merchant_id": merchant_id, "status": {"in": ["pending", "running"]}}
        )
        return SyncOperationOut.model_validate(sync) if sync else None

    async def update_progress(
        self,
        sync_id: str,
        processed: int,
        failed: int,
        progress_percent: int,
        message: str,
    ) -> None:
        """Update sync progress"""
        await self.prisma.syncoperation.update(
            where={"id": sync_id},
            data={
                "status": "running",
                "processed_products": processed,
                "failed_products": failed,
                "progress_percent": progress_percent,
                "progress_message": message,
            },
        )

    async def complete(self, sync_id: str, status: str, error_message: str | None = None) -> None:
        """Complete sync operation"""
        await self.prisma.syncoperation.update(
            where={"id": sync_id},
            data={
                "status": status,
                "completed_at": datetime.utcnow(),
                "error_message": error_message,
                "progress_percent": 100 if status == "completed" else None,
            },
        )
