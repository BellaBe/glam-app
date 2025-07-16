# services/webhook-service/src/repositories/platform_configuration_repository.py
"""Repository for platform configuration operations."""

from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.repository import Repository

from ..models.platform_configuration import PlatformConfiguration


class PlatformConfigurationRepository(Repository[PlatformConfiguration]):
    """Repository for platform configuration CRUD operations."""
    
    model = PlatformConfiguration
    
    async def find_by_platform(
        self,
        session: AsyncSession,
        platform: str
    ) -> Optional[PlatformConfiguration]:
        """Find platform configuration by platform name."""
        
        stmt = select(self.model).where(self.model.platform == platform)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_active_platforms(
        self,
        session: AsyncSession
    ) -> List[PlatformConfiguration]:
        """Find all active platform configurations."""
        
        stmt = (
            select(self.model)
            .where(self.model.active == True)
            .order_by(self.model.platform)
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
