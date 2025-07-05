from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,      
)

from shared.database import Repository
from ..models.notification import Notification, NotificationStatus, NotificationProvider

class NotificationRepository(Repository[Notification]):
    """Async Notification repo that opens a fresh session per call."""

    def __init__(
        self,
        model_class: type[Notification],
        session_factory: async_sessionmaker[AsyncSession],
    ):
        super().__init__(model_class, session_factory)

    # ------------------------------------------------------------------ helpers
    async def _session(self):
        """Async context manager that yields a short-lived session."""
        async with self.session_factory() as session:
            yield session

    # ------------------------------------------------------------------ queries
    async def get_by_shop_id(
        self,
        shop_id: UUID,
        limit: int = 100,
    ) -> List[Notification]:
        stmt = (
            select(self.model).where(self.model.shop_id == shop_id).order_by(self.model.created_at.desc()).limit(limit)
        )
        async for session in self._session():
            result = await session.execute(stmt)
            return list(result.scalars().all())
        return []

    async def get_by_status(
        self,
        status: NotificationStatus,
        limit: int = 100,
    ) -> List[Notification]:
        stmt = (
            select(self.model)
            .where(self.model.status == status)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        async for session in self._session():
            result = await session.execute(stmt)
            return list(result.scalars().all())
        return []

    async def get_failed_for_retry(
        self,
        max_retries: int = 3,
    ) -> List[Notification]:
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == "failed",
                    self.model.retry_count < max_retries,
                )
            )
            .order_by(self.model.created_at)
        )
        async for session in self._session():
            result = await session.execute(stmt)
            return list(result.scalars().all())
        
        return []

    async def count_by_type_and_shop(
        self,
        shop_id: UUID,
        notification_type: str,
        since: Optional[datetime] = None,
    ) -> int:
        stmt = select(func.count(self.model.id)).where(
            and_(
                self.model.shop_id == shop_id,
                self.model.type == notification_type,
            )
        )
        if since:
            stmt = stmt.where(self.model.created_at >= since)

        async for session in self._session():
            result = await session.execute(stmt)
            return result.scalar() or 0
        
        return 0

    async def get_stats(
        self,
        shop_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        base_query = select(
            self.model.status,
            func.count(self.model.id).label("count"),
        )
        if shop_id:
            base_query = base_query.where(self.model.shop_id == shop_id)
        base_query = base_query.group_by(self.model.status)

        type_query = select(
            self.model.type,
            func.count(self.model.id).label("count"),
        )
        if shop_id:
            type_query = type_query.where(self.model.shop_id == shop_id)
        type_query = type_query.group_by(self.model.type)

        async for session in self._session():
            status_rows = await session.execute(base_query)
            stats = {row.status: row.count for row in status_rows}
            type_rows = await session.execute(type_query)
            type_stats = {row.type: row.count for row in type_rows}

            return {
                "by_status": stats,
                "by_type": type_stats,
                "total": sum(
                    int(v) for v in stats.values() if isinstance(v, (int, float))
                ),
            }
        return {}

    async def get_by_id(
        self,
        notification_id: UUID,
    ) -> Optional[Notification]:
        stmt = select(self.model).where(self.model.id == notification_id)
        async for session in self._session():
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list(
        self,
        shop_id: Optional[UUID] = None,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        offset: int = 1,
        limit: int = 50,
    ) -> tuple[list[Notification], int]:
        """List notifications with optional filters.
        Args:
            shop_id (Optional[UUID]): Filter by shop ID.
            status (Optional[str]): Filter by notification status.
            notification_type (Optional[str]): Filter by notification type.
            offset (int): Pagination offset.
            limit (int): Number of records to return.
            
        Returns:
            total (int): Total number of notifications.
            notifications (List[Notification]): List of notifications matching the filters.
        
        """
        stmt = select(self.model)
        
        if shop_id:
            stmt = stmt.where(self.model.shop_id == shop_id)
        if status:
            stmt = stmt.where(self.model.status == status)
        if notification_type:
            stmt = stmt.where(self.model.type == notification_type)

        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset((offset - 1) * limit).limit(limit)
        total_stmt = select(func.count(self.model.id)).select_from(self.model)

        async for session in self._session():
            result = await session.execute(stmt)
            notifications = result.scalars().all()

            total_result = await session.execute(total_stmt)
            total = total_result.scalar_one_or_none() or 0

            return list(notifications), total

        return [], 0
    
    # ---------------------------------------------------------------- updates
    async def mark_as_sent(
        self,
        notification_id: UUID,
        provider_message_id: str,
        provider: NotificationProvider,
    ) -> Notification: # type: ignore[return]
        
        async for session in self._session():
            stmt = select(self.model).where(self.model.id == notification_id)
            result = await session.execute(stmt)
            notification = result.scalar_one_or_none()

            if not notification:
                raise ValueError(f"Notification {notification_id} not found")

            notification.status = NotificationStatus.SENT
            notification.provider_message_id = provider_message_id
            notification.provider = provider
            notification.sent_at = datetime.now(timezone.utc)

            session.add(notification)
            await session.commit()
            return notification

    async def mark_as_failed(
        self,
        notification_id: UUID,
        error_message: str,
        retry_count: int,
    ) -> Notification: # type: ignore[return]
        
        async for session in self._session():
            stmt = select(self.model).where(self.model.id == notification_id)
            result = await session.execute(stmt)
            notification = result.scalar_one_or_none()

            if not notification:
                raise ValueError(f"Notification {notification_id} not found")

            notification.status = NotificationStatus.FAILED
            notification.error_message = error_message
            notification.retry_count += retry_count
            notification.sent_at = datetime.now(timezone.utc)

            session.add(notification)
            await session.commit()
            return notification
        
   # ------------------------------------------------------------------ create
    async def create(
        self,
        notification: Notification,
    ) -> Notification: # type: ignore[return]
        async for session in self._session():
            session.add(notification)
            await session.commit()
            return notification

    async def bulk_create(
        self,
        notifications: List[Notification],
    ) -> List[Notification]:
        async for session in self._session():
            session.add_all(notifications)
            await session.commit()
            return notifications
        return []