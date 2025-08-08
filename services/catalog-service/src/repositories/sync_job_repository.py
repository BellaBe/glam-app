from typing import Optional, List
from datetime import datetime
from prisma import Prisma
from prisma.models import SyncJob

class SyncJobRepository:
    """Repository for SyncJob operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def create(self, shop_domain: str, sync_type: str = "full") -> SyncJob:
        """Create new sync job"""
        return await self.prisma.syncjob.create(
            data={
                "shopDomain": shop_domain,
                "type": sync_type,
                "status": "queued",
                "analysisStatus": "idle"
            }
        )
    
    async def find_by_id(self, sync_id: str) -> Optional[SyncJob]:
        """Find sync job by ID"""
        return await self.prisma.syncjob.find_unique(
            where={"id": sync_id}
        )
    
    async def find_active_sync(self, shop_domain: str) -> Optional[SyncJob]:
        """Find active sync for shop (status in ['queued', 'running'])"""
        return await self.prisma.syncjob.find_first(
            where={
                "shopDomain": shop_domain,
                "status": {"in": ["queued", "running"]}
            }
        )
    
    async def update_status(self, sync_id: str, status: str) -> SyncJob:
        """Update sync job status"""
        data = {"status": status}
        if status == "synced" or status == "failed":
            data["finishedAt"] = datetime.utcnow()
        
        return await self.prisma.syncjob.update(
            where={"id": sync_id},
            data=data
        )
    
    async def update_analysis_status(self, sync_id: str, analysis_status: str) -> SyncJob:
        """Update analysis status"""
        return await self.prisma.syncjob.update(
            where={"id": sync_id},
            data={"analysisStatus": analysis_status}
        )
    
    async def update_counts(self, sync_id: str, total_products: int, total_variants: int) -> SyncJob:
        """Update total counts from catalog.counted event"""
        return await self.prisma.syncjob.update(
            where={"id": sync_id},
            data={
                "totalProducts": total_products,
                "totalVariants": total_variants
            }
        )
    
    async def increment_submitted(self, sync_id: str) -> SyncJob:
        """Increment submitted items count"""
        return await self.prisma.syncjob.update(
            where={"id": sync_id},
            data={"submittedItems": {"increment": 1}}
        )
    
    async def increment_completed(self, sync_id: str) -> SyncJob:
        """Increment completed items count"""
        return await self.prisma.syncjob.update(
            where={"id": sync_id},
            data={"completedItems": {"increment": 1}}
        )
    
    async def increment_failed(self, sync_id: str) -> SyncJob:
        """Increment failed items count"""
        return await self.prisma.syncjob.update(
            where={"id": sync_id},
            data={"failedItems": {"increment": 1}}
        )
    
    async def fail_sync(self, sync_id: str, error_message: str) -> SyncJob:
        """Mark sync as failed with error"""
        return await self.prisma.syncjob.update(
            where={"id": sync_id},
            data={
                "status": "failed",
                "errorMessage": error_message,
                "finishedAt": datetime.utcnow()
            }
        )
    
    async def get_latest_sync(self, shop_domain: str) -> Optional[SyncJob]:
        """Get most recent sync for shop"""
        return await self.prisma.syncjob.find_first(
            where={"shopDomain": shop_domain},
            order_by={"createdAt": "desc"}
        )

# ================================================================
