# services/notification-service/src/repositories/notification_repository.py
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from prisma import Prisma

from ..schemas.notification import NotificationAttemptOut, NotificationOut, NotificationStats, NotificationStatus


class NotificationRepository:
    """Repository for notification data access"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    # Notification methods
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

    async def update(self, notification_id: UUID, data: dict[str, Any]) -> NotificationOut:
        """Update notification"""
        notification = await self.prisma.notification.update(where={"id": str(notification_id)}, data=data)
        return NotificationOut.model_validate(notification)

    async def find_many(
        self, filters: dict[str, Any] = None, skip: int = 0, limit: int = 50, order_by: list[tuple] = None
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

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count notifications with filters"""
        where = filters or {}
        return await self.prisma.notification.count(where=where)

    # Attempt methods
    async def create_attempt(self, data: dict[str, Any]) -> NotificationAttemptOut:
        """Create a new notification attempt record"""
        attempt = await self.prisma.notificationattempt.create(data=data)
        return NotificationAttemptOut.model_validate(attempt)

    async def get_attempt_count(self, notification_id: UUID) -> int:
        """Get count of attempts for a notification"""
        return await self.prisma.notificationattempt.count(where={"notification_id": str(notification_id)})

    async def get_attempts(self, notification_id: UUID) -> list[NotificationAttemptOut]:
        """Get all attempts for a notification"""
        attempts = await self.prisma.notificationattempt.find_many(
            where={"notification_id": str(notification_id)}, order={"attempt_number": "asc"}
        )
        return [NotificationAttemptOut.model_validate(a) for a in attempts]

    # Special queries
    async def find_retriable_notifications(self, max_attempts: int) -> list[NotificationOut]:
        """Find failed notifications with fewer than max attempts"""
        # Raw query to find failed notifications with attempt count
        results = await self.prisma.query_raw(
            """
            SELECT n.*
            FROM notifications n
            LEFT JOIN (
                SELECT notification_id, COUNT(*) as attempt_count
                FROM notification_attempts
                GROUP BY notification_id
            ) a ON n.id = a.notification_id
            WHERE n.status = 'failed'
            AND (a.attempt_count IS NULL OR a.attempt_count < $1)
            ORDER BY n.created_at DESC
            LIMIT 100
            """,
            max_attempts,
        )

        return [NotificationOut.model_validate(r) for r in results]

    async def get_stats(self) -> NotificationStats:
        """Get notification statistics"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Count by status today
        sent_today = await self.prisma.notification.count(
            where={"status": NotificationStatus.SENT, "created_at": {"gte": today_start, "lt": today_end}}
        )

        failed_today = await self.prisma.notification.count(
            where={"status": NotificationStatus.FAILED, "created_at": {"gte": today_start, "lt": today_end}}
        )

        pending_today = await self.prisma.notification.count(
            where={"status": NotificationStatus.PENDING, "created_at": {"gte": today_start, "lt": today_end}}
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
        by_status = {"sent": sent_today, "failed": failed_today, "pending": pending_today}

        return NotificationStats(
            sent_today=sent_today,
            failed_today=failed_today,
            pending_today=pending_today,
            by_template=by_template,
            by_status=by_status,
        )
