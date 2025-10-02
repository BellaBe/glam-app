# services/merchant-service/src/repositories/merchant_repository.py
from datetime import UTC, datetime

from prisma import Prisma  # type: ignore[attr-defined]
from prisma.enums import MerchantStatus
from prisma.models import Merchant

from ..schemas.merchant import MerchantSyncIn


class MerchantRepository:
    """Repository for Merchant operations using Prisma."""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def find_by_platform_identity(
        self, *, platform_name: str, domain: str, platform_shop_id: str | None
    ) -> Merchant | None:
        """
        Resolve merchant by identity with deterministic precedence:
        1) platform_shop_id (unique per platform)
        2) domain (unique per platform)
        """
        if platform_shop_id:
            m = await self.prisma.merchant.find_first(
                where={"platform_name": platform_name, "platform_shop_id": platform_shop_id}
            )
            if m:
                return m

        return await self.prisma.merchant.find_first(where={"platform_name": platform_name, "domain": domain.lower()})

    async def create(self, *, platform_name: str, domain: str, data: MerchantSyncIn) -> Merchant:
        """Create new merchant on first sync."""
        now = datetime.now(UTC)
        return await self.prisma.merchant.create(
            data={
                "platform_name": platform_name,
                "platform_shop_id": data.platform_shop_id,
                "domain": domain.lower(),
                "name": data.shop_name,
                "email": data.email,
                "primary_domain": data.primary_domain,  # <- fixed name
                "currency": data.currency,
                "country": data.country,
                "platform_version": data.platform_version,
                "scopes": data.scopes,
                "status": MerchantStatus.PENDING,
                "installed_at": now,
                "last_synced_at": now,
            }
        )

    async def update_for_sync(self, *, merchant_id: str, data: MerchantSyncIn) -> Merchant:
        """
        Update merchant on recurring sync (or reinstall after status update).
        NOTE: we DO NOT clear `uninstalled_at`; we keep the history.
        """
        return await self.prisma.merchant.update(
            where={"id": merchant_id},
            data={
                "name": data.shop_name,
                "email": data.email,
                "primary_domain": data.primary_domain,  # <- fixed name
                "currency": data.currency,
                "country": data.country,
                "platform_version": data.platform_version,
                "scopes": data.scopes,
                "last_synced_at": datetime.now(UTC),
            },
        )

    async def mark_reinstalled(self, *, merchant_id: str) -> Merchant:
        """Transition UNINSTALLED -> PENDING and stamp installed_at (keep uninstalled_at as history)."""
        return await self.prisma.merchant.update(
            where={"id": merchant_id},
            data={
                "status": MerchantStatus.PENDING,
                "installed_at": datetime.now(UTC),
                # uninstalled_at: keep as-is (historical)
            },
        )

    async def mark_uninstalled(self, *, merchant_id: str) -> Merchant:
        """Mark merchant as uninstalled and stamp uninstalled_at."""
        now = datetime.now(UTC)
        return await self.prisma.merchant.update(
            where={"id": merchant_id},
            data={"status": MerchantStatus.UNINSTALLED, "uninstalled_at": now},
        )

    async def update_status(self, *, merchant_id: str, new_status: MerchantStatus) -> Merchant:
        """Generic status update for internal transitions."""
        return await self.prisma.merchant.update(where={"id": merchant_id}, data={"status": new_status})
