from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database import Repository
from ..models import TrialExtension


class TrialExtensionRepository(Repository[TrialExtension]):
    """DB helpers for trial‑extension rows."""

    def __init__(self, model_class: type[TrialExtension], session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(model_class, session_factory)

    async def find_by_merchant_id(self, merchant_id: UUID) -> List[TrialExtension]:
        """All non‑revoked extensions (oldest‑>newest)."""
        async for session in self._session():
            stmt = (
                select(self.model)
                .where(
                    self.model.merchant_id == merchant_id,
                    self.model.revoked.is_(False),
                )
                .order_by(self.model.created_at)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
        return []

    async def count_by_merchant_id(self, merchant_id: UUID) -> int:
        async for session in self._session():
            stmt = (
                select(func.count())
                .select_from(self.model)
                .where(
                    self.model.merchant_id == merchant_id,
                    self.model.revoked.is_(False),
                )
            )
            result = await session.execute(stmt)
            return int(result.scalar_one())
        return 0

    async def latest_trial_end(self, merchant_id: UUID) -> datetime | None:
        """Return the most recently effective trial‑end date, or None."""
        async for session in self._session():
            stmt = (
                select(func.max(self.model.new_trial_end))
                .where(
                    self.model.merchant_id == merchant_id,
                    self.model.revoked.is_(False),
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one()
        return None
