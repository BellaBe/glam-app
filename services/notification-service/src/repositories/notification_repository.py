# services/notification-service/src/repositories/notification_repository.py
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from prisma import Prisma  # type: ignore[attr-defined]

from ..schemas.notification import NotificationOut, NotificationStats


class NotificationRepository:
    """Repository for notification data access"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def create(self, data: dict[str, Any]) -> NotificationOut:
        """Create a new notification record"""
        notification = await self.prisma.notification.create(data=data)
        return NotificationOut.model_validate(notification)

    async def find_by_id(self, notification_id: UUID) -> NotificationOut | None:
        """Find notification by ID"""
        notification = await self.prisma.notification.find_unique(where={"id": str(notification_id)})
        return NotificationOut.model_validate(notification) if notification else None

    async def find_by_idempotency_key(self, idempotency_key: str) -> NotificationOut | None:
        """Find notification by idempotency key"""
        notification = await self.prisma.notification.find_unique(where={"idempotency_key": idempotency_key})
        return NotificationOut.model_validate(notification) if notification else None

    async def find_many(
        self,
        filters: dict[str, Any] | None,
        order_by: list[tuple] | None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NotificationOut]:
        """Find multiple notifications with filters"""
        where = filters or {}
        order = {}

        if order_by:
            for field, direction in order_by:
                order[field] = direction
        else:
            order = {"created_at": "desc"}

        notifications = await self.prisma.notification.find_many(where=where, skip=skip, take=limit, order=order)

        return [NotificationOut.model_validate(n) for n in notifications]

    async def count(self, filters: dict[str, Any] | None) -> int:
        """Count notifications with filters"""
        where = filters or {}
        return await self.prisma.notification.count(where=where)

    async def update(self, notification_id: UUID, data: dict[str, Any]) -> NotificationOut:
        """Update notification"""
        notification = await self.prisma.notification.update(where={"id": str(notification_id)}, data=data)
        return NotificationOut.model_validate(notification)

    async def get_stats(self) -> NotificationStats:
        """Get notification statistics"""
        # Get today's date range
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Count by status today
        sent_today = await self.prisma.notification.count(
            where={
                "status": "sent",
                "created_at": {"gte": today_start, "lt": today_end},
            }
        )

        failed_today = await self.prisma.notification.count(
            where={
                "status": "failed",
                "created_at": {"gte": today_start, "lt": today_end},
            }
        )

        pending_today = await self.prisma.notification.count(
            where={
                "status": "pending",
                "created_at": {"gte": today_start, "lt": today_end},
            }
        )

        # Get counts by template type
        template_counts = await self.prisma.query_raw(
            """
            SELECT template_type, COUNT(*) as count
            FROM notifications
            WHERE created_at >= $1 AND created_at < $2
            GROUP BY template_type
            """,
            today_start,
            today_end,
        )

        by_template = {row["template_type"]: row["count"] for row in template_counts}

        # Get counts by status
        status_counts = await self.prisma.query_raw(
            """
            SELECT status, COUNT(*) as count
            FROM notifications
            WHERE created_at >= $1 AND created_at < $2
            GROUP BY status
            """,
            today_start,
            today_end,
        )

        by_status = {row["status"]: row["count"] for row in status_counts}

        return NotificationStats(
            sent_today=sent_today,
            failed_today=failed_today,
            pending_today=pending_today,
            by_template=by_template,
            by_status=by_status,
        )
