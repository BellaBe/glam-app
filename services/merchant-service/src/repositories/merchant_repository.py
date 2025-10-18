# services/merchant-service/src/repositories/merchant_repository.py
from __future__ import annotations
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Merchant, MerchantStatus
from src.schemas.merchant import MerchantSyncIn


class MerchantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, merchant_id: UUID | str) -> Merchant | None:
        """Find merchant by ID"""
        return await self.session.get(Merchant, str(merchant_id))

    async def find_by_platform_and_domain(
        self,
        platform_name: str,
        domain: str
    ) -> Merchant | None:
        """Find merchant by platform and domain"""
        stmt = select(Merchant).where(
            and_(
                Merchant.platform_name == platform_name,
                Merchant.domain == domain
            )
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def find_by_platform_and_shop(
        self,
        platform_name: str,
        platform_shop_id: str
    ) -> Merchant | None:
        """Find merchant by platform and shop ID"""
        stmt = select(Merchant).where(
            and_(
                Merchant.platform_name == platform_name,
                Merchant.platform_shop_id == platform_shop_id
            )
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def create(
        self,
        platform_name: str,
        data: MerchantSyncIn
    ) -> Merchant:
        """Create new merchant"""
        now = datetime.now(UTC)
        merchant = Merchant(
            platform_name=platform_name,
            platform_shop_id=data.platform_shop_id,
            domain=data.domain,
            name=data.name,
            email=data.email,
            primary_domain=data.primary_domain,
            currency=data.currency,
            country=data.country,
            platform_version=data.platform_version,
            scopes=data.scopes,
            status=MerchantStatus.PENDING,
            installed_at=now,
            last_synced_at=now
        )
        self.session.add(merchant)
        await self.session.flush()
        await self.session.refresh(merchant)
        return merchant

    async def update_from_sync(
        self,
        merchant: Merchant,
        data: MerchantSyncIn
    ) -> Merchant:
        """Update merchant from sync data"""
        now = datetime.now(UTC)
        
        merchant.name = data.name
        merchant.email = data.email
        merchant.primary_domain = data.primary_domain
        merchant.currency = data.currency
        merchant.country = data.country
        merchant.platform_version = data.platform_version
        merchant.scopes = data.scopes
        merchant.last_synced_at = now

        # If reinstalling, clear uninstall timestamp and update status
        if merchant.status == MerchantStatus.UNINSTALLED:
            merchant.uninstalled_at = None
            merchant.installed_at = now
            merchant.status = MerchantStatus.PENDING

        await self.session.flush()
        await self.session.refresh(merchant)
        return merchant

    async def update_status(
        self,
        merchant: Merchant,
        new_status: MerchantStatus
    ) -> Merchant:
        """Update merchant status"""
        merchant.status = new_status
        
        if new_status == MerchantStatus.UNINSTALLED:
            merchant.uninstalled_at = datetime.now(UTC)
        
        await self.session.flush()
        await self.session.refresh(merchant)
        return merchant

