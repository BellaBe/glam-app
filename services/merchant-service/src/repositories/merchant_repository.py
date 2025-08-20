# services/merchant-service/src/repositories/merchant_repository.py
from datetime import UTC, datetime

from prisma import Prisma  # type: ignore[attr-defined]
from prisma.enums import MerchantStatus
from prisma.models import Merchant

from ..schemas.merchant import MerchantSyncIn


class MerchantRepository:
    """Repository for Merchant operations using Prisma"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def find_by_platform_shop_identity(
        self, platform_name: str, shop_domain: str, platform_shop_id: str | None = None
    ) -> Merchant | None:
        """Find merchant by platform identity"""
        conditions = [{"platform_name": platform_name, "shop_domain": shop_domain.lower()}]
        if platform_shop_id:
            conditions.append({"platform_name": platform_name, "platform_shop_id": platform_shop_id})

        return await self.prisma.merchant.find_first(where={"OR": conditions})

    async def find_by_shop_domain(self, shop_domain: str) -> Merchant | None:
        """Find merchant by platform domain"""
        return await self.prisma.merchant.find_first(where={"shop_domain": shop_domain.lower()})

    async def create(self, data: MerchantSyncIn) -> Merchant:
        """Create new merchant"""
        return await self.prisma.merchant.create(
            data={
                "platform_name": data.platform_name.lower(),
                "platform_shop_id": data.platform_shop_id,
                "shop_domain": data.shop_domain.lower(),  # myshopify domain
                "name": data.shop_name,
                "email": data.email,
                "primary_domain": data.primary_domain_host,  # could be custom domain
                "currency": data.currency,
                "country": data.country,
                "platform_version": data.platform_version,
                "scopes": data.scopes,
                "status": MerchantStatus.PENDING,
                "installed_at": datetime.now(UTC),
                "last_sync_at": datetime.now(UTC),
            }
        )

    async def update_for_sync(self, merchant_id: str, data: MerchantSyncIn) -> Merchant:
        """Update merchant on sync (reinstall or resync)"""
        return await self.prisma.merchant.update(
            where={"id": merchant_id},
            data={
                "name": data.shop_name,
                "email": data.email,
                "primary_domain": data.primary_domain_host,
                "currency": data.currency,
                "country": data.country,
                "platform_version": data.platform_version,
                "scopes": data.scopes,
                "last_sync_at": datetime.utcnow(),
                "uninstalled_at": None,  # Clear if reinstalling
            },
        )

    async def update_status(self, merchant_id: str, new_status: MerchantStatus) -> Merchant:
        """Update merchant status"""
        update_data = {"status": new_status, "status_changed_at": datetime.utcnow()}

        # Set uninstalled_at if uninstalling
        if new_status == MerchantStatus.UNINSTALLED:
            update_data["uninstalled_at"] = datetime.utcnow()

        return await self.prisma.merchant.update(where={"id": merchant_id}, data=update_data)
