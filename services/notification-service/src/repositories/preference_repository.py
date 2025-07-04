"""
PreferenceRepository  ❖  DB wrapper for `NotificationPreference`

* Accepts an **async_sessionmaker** (session-factory pattern)
* Opens a fresh `AsyncSession` inside every public method
"""

from __future__ import annotations

from typing import Optional, List, AsyncIterator
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database import Repository
from ..models.entities import NotificationPreference


class PreferenceRepository(Repository[NotificationPreference]):
    """Async repo for per-shop notification preferences."""

    # ------------------------------------------------------------------ init
    def __init__(
        self,
        model_class: type[NotificationPreference],
        session_factory: async_sessionmaker[AsyncSession],
    ):
        super().__init__(model_class, session_factory)

    # ---------------------------------------------------------------- helper
    async def _session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session

    # ----------------------------------------------------------- read methods
    async def get_by_shop_id(
        self,
        shop_id: UUID,
    ) -> Optional[NotificationPreference]:
        stmt = select(self.model).where(self.model.shop_id == shop_id)
        async for s in self._session():
            res = await s.execute(stmt)
            return res.scalar_one_or_none()

    async def get_by_unsubscribe_token(
        self,
        token: str,
    ) -> Optional[NotificationPreference]:
        stmt = select(self.model).where(self.model.unsubscribe_token == token)
        async for s in self._session():
            res = await s.execute(stmt)
            return res.scalar_one_or_none()

    async def get_subscribed_shops(
        self,
        notification_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[NotificationPreference]:
        """
        Return shops whose JSONB `notification_types[notification_type]` flag
        is true *and* email delivery is enabled.
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.email_enabled.is_(True),
                    self.model.notification_types[notification_type].astext
                    == "true",
                )
            )
            .offset(skip)
            .limit(limit)
        )
        async for s in self._session():
            res = await s.execute(stmt)
            return list(res.scalars().all())
        return []

    # ----------------------------------------------------------- write / upsert
    async def bulk_create_or_update(
        self,
        preferences: List[NotificationPreference],
    ) -> List[NotificationPreference]:
        """
        For each incoming `NotificationPreference`:
        • update existing row (matched on shop_id) or  
        • insert new row  
        Returns the list of objects as persisted.
        """
        updated: List[NotificationPreference] = []

        async for session in self._session():
            for pref in preferences:
                if not isinstance(pref.shop_id, UUID):
                    raise ValueError("shop_id must be a UUID")

                existing = await session.scalar(
                    select(self.model).where(self.model.shop_id == pref.shop_id)
                )

                if existing:
                    # update mutable columns
                    for field, value in pref.__dict__.items():
                        if hasattr(existing, field):
                            setattr(existing, field, value)
                    obj = existing
                else:
                    obj = self.model(**pref.__dict__)
                    session.add(obj)

                updated.append(obj)

            await session.commit()
        return updated
