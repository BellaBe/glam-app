# services/merchant-service/src/repositories/merchant.py
from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from datetime import datetime
from shared.database.repository import Repository
from ..models.merchant import Merchant
from ..models.merchant_status import MerchantStatus
from ..models.merchant_configuration import MerchantConfiguration
from ..models.installation_record import InstallationRecord

class MerchantRepository(Repository[Merchant]):
    """Repository for merchant operations"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(Merchant, session_factory)
    
    # Core read operations
    async def get_by_shop_id(self, shop_id: str) -> Optional[Merchant]:
        """Get merchant by Shopify shop ID"""
        async for session in self._session():
            stmt = select(Merchant).where(Merchant.shop_id == shop_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_with_status(self, merchant_id: UUID) -> Optional[Merchant]:
        """Get merchant with status relation"""
        async for session in self._session():
            stmt = (
                select(Merchant)
                .options(selectinload(Merchant.status))
                .where(Merchant.id == merchant_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_with_all_relations(self, merchant_id: UUID) -> Optional[Merchant]:
        """Get merchant with all relations"""
        async for session in self._session():
            stmt = (
                select(Merchant)
                .options(
                    selectinload(Merchant.status),
                    selectinload(Merchant.configuration),
                    selectinload(Merchant.installation_records)
                )
                .where(Merchant.id == merchant_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def lookup_by_platform(self, platform: str, external_id: str) -> Optional[Merchant]:
        """Lookup merchant by platform-specific external ID"""
        if platform == "shopify":
            return await self.get_by_shop_id(external_id)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    # Core write operations
    async def create_merchant(self, merchant: Merchant) -> Merchant | None:
        """Create a new merchant"""
        async for session in self._session():
            session.add(merchant)
            await session.commit()
            await session.refresh(merchant)
            return merchant
    
    async def create_status(self, status: MerchantStatus) -> MerchantStatus | None:
        """Create merchant status"""
        async for session in self._session():
            session.add(status)
            await session.commit()
            await session.refresh(status)
            return status
    
    async def update_status(self, status: MerchantStatus) -> MerchantStatus | None:
        """Update merchant status"""
        async for session in self._session():
            status.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(status)
            return status
    
    async def create_configuration(self, config: MerchantConfiguration) -> MerchantConfiguration | None:
        """Create merchant configuration"""
        async for session in self._session():
            session.add(config)
            await session.commit()
            await session.refresh(config)
            return config
    
    async def update_configuration(self, config: MerchantConfiguration) -> MerchantConfiguration | None:
        """Update merchant configuration"""
        async for session in self._session():
            config.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(config)
            return config
    
    async def update_last_activity(self, merchant_id: UUID) -> None:
        """Update last activity timestamp"""
        async for session in self._session():
            await session.execute(
                update(MerchantStatus)
                .where(MerchantStatus.merchant_id == merchant_id)
                .values(
                    last_activity_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
    
    async def create_installation_record(self, record: InstallationRecord) -> InstallationRecord | None:
        """Create installation record"""
        async for session in self._session():
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record
    
    async def get_latest_installation_record(self, merchant_id: UUID, platform: str) -> InstallationRecord | None:
        """Get the most recent installation record for a platform"""
        async for session in self._session():
            stmt = (
                select(InstallationRecord)
                .where(
                    InstallationRecord.merchant_id == merchant_id,
                    InstallationRecord.platform == platform
                )
                .order_by(InstallationRecord.installed_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
