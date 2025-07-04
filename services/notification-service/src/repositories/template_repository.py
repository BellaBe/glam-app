"""
TemplateRepository  ❖  DB wrapper for `NotificationTemplate`

* Accepts an **async_sessionmaker** (the session-factory pattern we adopted)
* Opens a fresh `AsyncSession` for every DB interaction
* Exposes only the methods the current TemplateService needs:
      • get_active_by_type()
      • get_by_id()
You can extend with upsert / list / delete later with the same pattern.
"""

from __future__ import annotations

from typing import Optional, AsyncIterator
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database import Repository
from ..models.entities import NotificationTemplate


class TemplateRepository(Repository[NotificationTemplate]):
    """Async repo for notification e-mail templates."""

    def __init__(
        self,
        model_class: type[NotificationTemplate],
        session_factory: async_sessionmaker[AsyncSession],
    ):
        super().__init__(model_class, session_factory)

    # -------------------------------------------------------------------- #
    # internal helper                                                      #
    # -------------------------------------------------------------------- #
    async def _session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session

    # -------------------------------------------------------------------- #
    # public API                                                           #
    # -------------------------------------------------------------------- #
    async def get_active_by_type(
        self,
        notification_type: str,
        at: Optional[datetime] = None,
    ) -> Optional[NotificationTemplate]:
        """
        Return the *currently active* template for the given type.
        If `at` is provided, returns the template that was active at that
        specific moment (useful for audits / historical rendering).
        """
        stmt = (
            select(self.model)
            .where(self.model.type == notification_type, self.model.is_active.is_(True))
            .order_by(self.model.created_at.desc())  # newest first
            .limit(1)
        )

        if at:
            stmt = stmt.where(self.model.created_at <= at)

        async for session in self._session():
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_id(
        self,
        template_id: UUID,
    ) -> Optional[NotificationTemplate]:
        stmt = select(self.model).where(self.model.id == template_id)
        async for session in self._session():
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
