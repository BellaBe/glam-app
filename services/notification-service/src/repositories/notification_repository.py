from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Notification, NotificationStatus
from ..schemas.notification import NotificationOut, NotificationStats


class NotificationRepository:
    """Repository for notification data access"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict[str, Any]) -> NotificationOut:
        """Create a new notification record"""
        try:
            notification = Notification(**data)
            self.session.add(notification)
            await self.session.flush()
            await self.session.refresh(notification)
            return NotificationOut.model_validate(notification)
        except Exception:
            raise

    async def find_by_id(self, notification_id: UUID) -> NotificationOut | None:
        """Find notification by ID"""
        notification = await self.session.get(Notification, str(notification_id))
        return NotificationOut.model_validate(notification) if notification else None

    async def find_by_idempotency_key(self, idempotency_key: str) -> NotificationOut | None:
        """Find notification by idempotency key"""
        stmt = select(Notification).where(Notification.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        notification = result.scalars().first()
        return NotificationOut.model_validate(notification) if notification else None

    async def update(self, notification_id: UUID, data: dict[str, Any]) -> NotificationOut:
        """Update notification"""
        notification = await self.session.get(Notification, str(notification_id))
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        for key, value in data.items():
            setattr(notification, key, value)

        await self.session.flush()
        await self.session.refresh(notification)
        return NotificationOut.model_validate(notification)

    async def find_many(
        self, filters: dict[str, Any] | None = None, skip: int = 0, limit: int = 50, order_by: list[tuple] | None = None
    ) -> list[NotificationOut]:
        """Find multiple notifications with filters"""
        stmt = select(Notification)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(Notification, key):
                    stmt = stmt.where(getattr(Notification, key) == value)

        # Apply ordering
        if order_by:
            for field, direction in order_by:
                col = getattr(Notification, field)
                stmt = stmt.order_by(col.desc() if direction == "desc" else col.asc())
        else:
            stmt = stmt.order_by(Notification.first_attempt_at.desc())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        notifications = result.scalars().all()

        return [NotificationOut.model_validate(n) for n in notifications]

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count notifications with filters"""
        stmt = select(func.count(Notification.id))

        if filters:
            for key, value in filters.items():
                if hasattr(Notification, key):
                    stmt = stmt.where(getattr(Notification, key) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_retriable(self, max_attempts: int = 3, limit: int = 50) -> list[NotificationOut]:
        """Find notifications eligible for retry"""
        stmt = (
            select(Notification)
            .where(and_(Notification.status == NotificationStatus.PENDING, Notification.attempt_count < max_attempts))
            .order_by(Notification.last_attempt_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        notifications = result.scalars().all()
        return [NotificationOut.model_validate(n) for n in notifications]

    async def count_recent_by_email(self, email: str, hours: int = 1) -> int:
        """Count recent notifications sent to an email (for rate limiting)"""
        since = datetime.now(UTC) - timedelta(hours=hours)

        stmt = select(func.count(Notification.id)).where(
            and_(Notification.recipient_email == email, Notification.first_attempt_at >= since)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_stats(self) -> NotificationStats:
        """Get notification statistics"""
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Count by status today
        sent_stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.status == NotificationStatus.SENT,
                Notification.first_attempt_at >= today_start,
                Notification.first_attempt_at < today_end,
            )
        )
        sent_result = await self.session.execute(sent_stmt)
        sent_today = sent_result.scalar_one()

        failed_stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.status == NotificationStatus.FAILED,
                Notification.first_attempt_at >= today_start,
                Notification.first_attempt_at < today_end,
            )
        )
        failed_result = await self.session.execute(failed_stmt)
        failed_today = failed_result.scalar_one()

        pending_stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.status == NotificationStatus.PENDING,
                Notification.first_attempt_at >= today_start,
                Notification.first_attempt_at < today_end,
            )
        )
        pending_result = await self.session.execute(pending_stmt)
        pending_today = pending_result.scalar_one()

        # Get counts by template type
        template_stmt = (
            select(Notification.template_type, func.count(Notification.id).label("count"))
            .where(and_(Notification.first_attempt_at >= today_start, Notification.first_attempt_at < today_end))
            .group_by(Notification.template_type)
            .order_by(Notification.template_type)
        )
        template_result = await self.session.execute(template_stmt)
        by_template = {row[0]: row[1] for row in template_result}

        # Get counts by status
        by_status = {
            "sent": sent_today,
            "failed": failed_today,
            "pending": pending_today,
        }

        return NotificationStats(
            sent_today=sent_today,
            failed_today=failed_today,
            pending_today=pending_today,
            by_template=by_template,
            by_status=by_status,
        )

    async def get_delivery_metrics(self) -> dict[str, Any]:
        """Get delivery performance metrics"""
        # Average delivery time for successful notifications
        from sqlalchemy import literal_column

        delivery_stmt = select(
            func.avg(func.extract("EPOCH", Notification.delivered_at - Notification.first_attempt_at)).label(
                "avg_delivery_seconds"
            ),
            func.min(func.extract("EPOCH", Notification.delivered_at - Notification.first_attempt_at)).label(
                "min_delivery_seconds"
            ),
            func.max(func.extract("EPOCH", Notification.delivered_at - Notification.first_attempt_at)).label(
                "max_delivery_seconds"
            ),
        ).where(and_(Notification.status == NotificationStatus.SENT, Notification.delivered_at.isnot(None)))

        delivery_result = await self.session.execute(delivery_stmt)
        delivery_row = delivery_result.first()

        # Attempt distribution
        attempt_stmt = (
            select(
                Notification.attempt_count,
                func.count(Notification.id).label("count"),
                func.round(
                    func.cast(func.count(Notification.id) * 100.0, type_=literal_column("numeric"))
                    / func.sum(func.count(Notification.id)).over(),
                    2,
                ).label("percentage"),
            )
            .where(Notification.status == NotificationStatus.SENT)
            .group_by(Notification.attempt_count)
            .order_by(Notification.attempt_count)
        )

        attempt_result = await self.session.execute(attempt_stmt)

        return {
            "delivery_time": {
                "avg_delivery_seconds": float(delivery_row[0]) if delivery_row[0] else None,
                "min_delivery_seconds": float(delivery_row[1]) if delivery_row[1] else None,
                "max_delivery_seconds": float(delivery_row[2]) if delivery_row[2] else None,
            }
            if delivery_row
            else None,
            "attempt_distribution": [
                {"attempts": row[0], "count": row[1], "percentage": float(row[2]) if row[2] else 0.0}
                for row in attempt_result
            ],
        }

    async def cleanup_old_notifications(self, days: int = 30) -> int:
        """Delete old notifications (for data retention)"""
        from sqlalchemy import delete

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        # Count before deletion
        count_stmt = select(func.count(Notification.id)).where(Notification.first_attempt_at < cutoff_date)
        count_result = await self.session.execute(count_stmt)
        count = count_result.scalar_one()

        # Delete old notifications
        if count > 0:
            delete_stmt = delete(Notification).where(Notification.first_attempt_at < cutoff_date)
            await self.session.execute(delete_stmt)

        return count
