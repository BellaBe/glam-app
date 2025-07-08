# File: services/connector-service/src/repositories/store_connection_repository.py

"""Repository for store connections."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from shared.database import Repository
from ..models.store_connection import StoreConnection, StoreStatus


class StoreConnectionRepository(Repository[StoreConnection]):
    """Repository for store connection operations."""
    
    async def get_by_store_id(self, store_id: str) -> Optional[StoreConnection]:
        """Get connection by store ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.store_id == store_id)
            )
            return result.scalars().first()
    
    async def get_active_stores(self, limit: int = 100, offset: int = 0) -> List[StoreConnection]:
        """Get all active store connections."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model)
                .where(self.model.status == StoreStatus.ACTIVE)
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
    
    async def update_last_used(self, store_id: str) -> None:
        """Update last used timestamp."""
        async with self.session_factory() as session:
            await session.execute(
                update(self.model)
                .where(self.model.store_id == store_id)
                .values(last_used_at=datetime.now(timezone.utc))
            )
            await session.commit()
    
    async def update_status(self, store_id: str, status: StoreStatus) -> None:
        """Update store connection status."""
        async with self.session_factory() as session:
            await session.execute(
                update(self.model)
                .where(self.model.store_id == store_id)
                .values(status=status, updated_at=datetime.now(timezone.utc))
            )
            await session.commit()