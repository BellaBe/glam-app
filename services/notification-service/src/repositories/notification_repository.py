# services/notification-service/src/repositories/notification_repository.py
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from prisma import Prisma

from ..schemas.notification import NotificationOut, NotificationStats, NotificationStatus


class NotificationRepository:
    """Repository for notification data access"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def create(self, data: dict[str, Any]) -> NotificationOut:
        """Create a new notification record"""
        try:
            notification = await self.prisma.notification.create(data=data)
            return NotificationOut.model_validate(notification)
        except Exception:
            raise

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
            order = {"first_attempt_at": "desc"}  # Changed from created_at

        notifications = await self.prisma.notification.find_many(where=where, skip=skip, take=limit, order=order)

        return [NotificationOut.model_validate(n) for n in notifications]

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count notifications with filters"""
        where = filters or {}
        return await self.prisma.notification.count(where=where)

    async def find_retriable(self, max_attempts: int = 3, limit: int = 50) -> list[NotificationOut]:
        """Find notifications eligible for retry"""
        notifications = await self.prisma.notification.find_many(
            where={"status": NotificationStatus.PENDING, "attempt_count": {"lt": max_attempts}},
            order={"last_attempt_at": "asc"},  # Retry oldest first
            take=limit,
        )
        return [NotificationOut.model_validate(n) for n in notifications]

    async def count_recent_by_email(self, email: str, hours: int = 1) -> int:
        """Count recent notifications sent to an email (for rate limiting)"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return await self.prisma.notification.count(
            where={"recipient_email": email, "first_attempt_at": {"gte": since}}
        )

    async def get_stats(self) -> NotificationStats:
        """Get notification statistics"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Count by status today (using first_attempt_at for "today's notifications")
        sent_today = await self.prisma.notification.count(
            where={"status": NotificationStatus.SENT, "first_attempt_at": {"gte": today_start, "lt": today_end}}
        )

        failed_today = await self.prisma.notification.count(
            where={"status": NotificationStatus.FAILED, "first_attempt_at": {"gte": today_start, "lt": today_end}}
        )

        pending_today = await self.prisma.notification.count(
            where={"status": NotificationStatus.PENDING, "first_attempt_at": {"gte": today_start, "lt": today_end}}
        )

        # Get counts by template type
        template_counts = await self.prisma.query_raw(
            """
            SELECT template_type, COUNT(*) as count
            FROM notifications
            WHERE first_attempt_at >= $1 AND first_attempt_at < $2
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

    async def get_delivery_metrics(self) -> dict[str, Any]:
        """Get delivery performance metrics"""
        # Average delivery time for successful notifications
        delivery_times = await self.prisma.query_raw(
            """
            SELECT
                AVG(EXTRACT(EPOCH FROM (delivered_at - first_attempt_at))) as avg_delivery_seconds,
                MIN(EXTRACT(EPOCH FROM (delivered_at - first_attempt_at))) as min_delivery_seconds,
                MAX(EXTRACT(EPOCH FROM (delivered_at - first_attempt_at))) as max_delivery_seconds
            FROM notifications
            WHERE status = 'sent' AND delivered_at IS NOT NULL
            """
        )

        # Attempt distribution
        attempt_distribution = await self.prisma.query_raw(
            """
            SELECT
                attempt_count,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM notifications
            WHERE status = 'sent'
            GROUP BY attempt_count
            ORDER BY attempt_count
            """
        )

        return {
            "delivery_time": delivery_times[0] if delivery_times else None,
            "attempt_distribution": [
                {"attempts": row["attempt_count"], "count": row["count"], "percentage": float(row["percentage"])}
                for row in attempt_distribution
            ],
        }

    async def cleanup_old_notifications(self, days: int = 30) -> int:
        """Delete old notifications (for data retention)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Count before deletion
        count = await self.prisma.notification.count(where={"first_attempt_at": {"lt": cutoff_date}})

        # Delete old notifications
        if count > 0:
            await self.prisma.notification.delete_many(where={"first_attempt_at": {"lt": cutoff_date}})

        return count
