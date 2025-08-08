from typing import Optional
from datetime import datetime
from prisma import Prisma
from prisma.models import MerchantCatalogState

class CatalogStateRepository:
    """Repository for MerchantCatalogState operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def upsert(self, shop_domain: str, data: dict) -> MerchantCatalogState:
        """Create or update merchant catalog state"""
        return await self.prisma.merchantcatalogstate.upsert(
            where={"shopDomain": shop_domain},
            data={
                "create": {
                    "shopDomain": shop_domain,
                    **data
                },
                "update": data
            }
        )
    
    async def find_by_shop_domain(self, shop_domain: str) -> Optional[MerchantCatalogState]:
        """Find catalog state by shop domain"""
        return await self.prisma.merchantcatalogstate.find_unique(
            where={"shopDomain": shop_domain}
        )
    
    async def update_settings(self, shop_domain: str, data_access: bool, auto_sync: bool, tos_accepted: bool) -> MerchantCatalogState:
        """Update merchant settings from event"""
        return await self.upsert(shop_domain, {
            "dataAccess": data_access,
            "autoSync": auto_sync,
            "tosAccepted": tos_accepted
        })
    
    async def update_entitlements(self, shop_domain: str, entitled: bool) -> MerchantCatalogState:
        """Update billing entitlements from event"""
        return await self.upsert(shop_domain, {
            "entitled": entitled
        })
    
    async def set_active_sync(self, shop_domain: str, sync_id: str) -> MerchantCatalogState:
        """Set active sync for merchant"""
        return await self.prisma.merchantcatalogstate.update(
            where={"shopDomain": shop_domain},
            data={
                "activeSyncId": sync_id,
                "hasSyncedBefore": True,
                "lastSyncAt": datetime.utcnow()
            }
        )
    
    async def clear_active_sync(self, shop_domain: str) -> MerchantCatalogState:
        """Clear active sync for merchant"""
        return await self.prisma.merchantcatalogstate.update(
            where={"shopDomain": shop_domain},
            data={"activeSyncId": None}
        )

# ================================================================
