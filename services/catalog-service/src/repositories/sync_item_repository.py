from typing import Optional, List
from prisma import Prisma
from prisma.models import SyncItem

class SyncItemRepository:
    """Repository for SyncItem operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def create(self, data: dict) -> SyncItem:
        """Create new sync item"""
        return await self.prisma.syncitem.create(data=data)
    
    async def exists(self, sync_id: str, variant_id: str) -> bool:
        """Check if item already exists for sync"""
        item = await self.prisma.syncitem.find_first(
            where={
                "syncId": sync_id,
                "variantId": variant_id
            }
        )
        return item is not None
    
    async def update_status(self, sync_id: str, variant_id: str, status: str, error: Optional[str] = None) -> SyncItem:
        """Update item status"""
        data = {"status": status}
        if error:
            data["error"] = error
        
        return await self.prisma.syncitem.update(
            where={
                "syncId_variantId": {
                    "syncId": sync_id,
                    "variantId": variant_id
                }
            },
            data=data
        )
    
    async def count_by_status(self, sync_id: str, status: str) -> int:
        """Count items by status"""
        return await self.prisma.syncitem.count(
            where={
                "syncId": sync_id,
                "status": status
            }
        )
    
    async def delete_by_sync(self, sync_id: str) -> int:
        """Delete all items for a sync (cleanup)"""
        result = await self.prisma.syncitem.delete_many(
            where={"syncId": sync_id}
        )
        return result.count

# ================================================================
