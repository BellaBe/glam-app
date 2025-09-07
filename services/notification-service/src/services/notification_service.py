# services/notification-service/src/services/notification_service.py
from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from prisma import Json
from prisma.errors import UniqueViolationError
from pydantic import BaseModel

from shared.messaging.events.base import BaseEventPayload
from shared.utils.exceptions import NotFoundError
from shared.utils.logger import ServiceLogger

from ..repositories.notification_repository import NotificationRepository
from ..schemas.notification import NotificationOut, NotificationStats, NotificationStatus
from .email_service import EmailService
from .template_service import TemplateService

T = TypeVar("T", bound=BaseModel)


class NotificationService:
    EMAIL_TEMPLATE_MAP = {
        "evt.merchant.created.v1": "welcome",
        "evt.billing.purchase.completed.v1": "purchase_confirmation",
        "evt.credit.trial.granted.v1": "trial_granted",
        "evt.credit.trial.low.v1": "trial_low",
        "evt.credit.trial.exhausted.v1": "trial_exhausted",
        "evt.credit.balance.granted.v1": "credit_granted",
        "evt.credit.balance.low.v1": "credit_low",
        "evt.credit.balance.exhausted.v1": "credit_exhausted",
        "evt.catalog.sync.started.v1": "catalog_sync_started",
        "evt.catalog.sync.completed.v1": "catalog_sync_completed",
        "evt.catalog.sync.failed.v1": "catalog_sync_failed",
        "evt.merchant.status.changed.v1": "account_deactivated",
    }

    def __init__(
        self,
        repository: NotificationRepository,
        template_service: TemplateService,
        email_service: EmailService,
        logger: ServiceLogger,
    ):
        self.repository = repository
        self.template_service = template_service
        self.email_service = email_service
        self.logger = logger

    async def process_event(
        self,
        event_type: str,
        data: T,
        event_id: str,
        correlation_id: str,
    ) -> NotificationOut | None:
        """
        Process event - NATS will retry this entire function up to 3 times.
        We track attempt_count for observability.
        """
        self.logger.info(
            "Processing event",
            extra={"event_type": event_type, "event_id": event_id, "correlation_id": correlation_id},
        )

        self.logger.info("Checking for existing notification", extra={"event_id": event_id})
        existing = await self.repository.find_by_idempotency_key(event_id)

        if existing:
            self.logger.info(
                "Found existing notification",
                extra={"notification_id": str(existing.id), "status": existing.status.value},
            )
            if existing.status == NotificationStatus.SENT:
                self.logger.info(f"Event {event_id} already delivered")
                return existing

            now = datetime.now()
            await self.repository.update(
                existing.id, {"attempt_count": existing.attempt_count + 1, "last_attempt_at": now}
            )

            self.logger.info(
                "Retrying delivery for existing notification",
                extra={"notification_id": str(existing.id), "attempt_count": existing.attempt_count + 1},
            )
            await self._send_email(existing, correlation_id)
            return await self.repository.find_by_id(existing.id)

        # New notification - validate and create
        email_template = self.EMAIL_TEMPLATE_MAP.get(event_type)
        if not email_template:
            self.logger.info("No template for event", extra={"event_type": event_type})
            return None

        # Handle conditional templates
        if event_type == "evt.merchant.status.changed.v1":
            status = getattr(data, "status", None)
            if status != "deactivated":
                self.logger.info("Skipping notification - status not deactivated", extra={"status": status})
                return None
            email_template = "account_deactivated"

        email = getattr(data, "email", None)
        if not email:
            self.logger.warning("No recipient email", extra={"event_type": event_type, "event_id": event_id})
            return None

        # Prepare notification data
        ids = data.identifiers
        variables = self._prepare_template_variables(event_type, data)
        now = datetime.now()

        new_notification = {
            "merchant_id": str(ids.merchant_id),
            "platform_name": ids.platform_name,
            "platform_shop_id": ids.platform_shop_id,
            "domain": ids.domain,
            "recipient_email": email,
            "template_type": email_template,
            "template_variables": Json(variables),
            "status": NotificationStatus.PENDING.value,
            "idempotency_key": event_id,
            "attempt_count": 1,
            "first_attempt_at": now,
            "last_attempt_at": now,
        }

        try:
            notification = await self.repository.create(new_notification)
        except UniqueViolationError:
            # Race condition - another process created it
            notification = await self.repository.find_by_idempotency_key(event_id)
            if notification.status == NotificationStatus.SENT:
                return notification

        # Send email
        await self._send_email(notification, correlation_id)
        return await self.repository.find_by_id(notification.id)

    async def _send_email(self, notification: dict, correlation_id: str) -> None:
        """
        Send email and update status. Raises exception for NATS retry if needed.
        """

        if notification.status == NotificationStatus.SENT:
            self.logger.info("Skip delivery: already sent", extra={"notification_id": str(notification.id)})
            return

        try:
            subject, html_body, text_body = self.template_service.render_email(
                notification.template_type, notification.template_variables
            )

            self.logger.info(f"Sending email to {notification.recipient_email}")

            response = await self.email_service.send(
                to=notification.recipient_email,
                subject=subject,
                html=html_body,
                text=text_body,
                metadata={
                    "notification_id": str(notification.id),
                    "merchant_id": notification.merchant_id,
                    "attempt": notification.attempt_count,
                    "template_type": notification.template_type,
                    "correlation_id": correlation_id,
                },
            )

            now = datetime.now()

            await self.repository.update(
                notification.id,
                {
                    "status": NotificationStatus.SENT.value,
                    "delivered_at": now,
                    "provider_message_id": response.get("message_id"),
                    "provider_message": Json(
                        {
                            "response": response,
                        }
                    ),
                },
            )

            self.logger.info(
                "Notification delivered",
                extra={
                    "notification_id": str(notification.id),
                    "attempt": notification.attempt_count,
                    "provider_message_id": response.get("message_id"),
                    "correlation_id": correlation_id,
                },
            )

        except Exception as e:
            error_msg = str(e)[:1000]  # Truncate long errors

            is_final_attempt = notification.attempt_count >= 3
            new_status = NotificationStatus.FAILED if is_final_attempt else NotificationStatus.PENDING

            # Update notification with failure
            await self.repository.update(
                notification.id,
                {
                    "status": new_status,
                    "last_attempt_at": datetime.now(),
                    "provider_message": Json(
                        {
                            "provider": self.email_service.provider_name,
                            "error": error_msg,
                        }
                    ),
                },
            )

            self.logger.exception(
                "Notification delivery failed",
                extra={
                    "notification_id": str(notification.id),
                    "attempt": notification.attempt_count,
                    "error": error_msg,
                    "final": is_final_attempt,
                },
            )

            # Re-raise for NATS retry (unless we've hit max attempts)
            if not is_final_attempt:
                raise

    def _prepare_template_variables(self, event_type: str, data: BaseEventPayload) -> dict:
        """Prepare template variables for email rendering."""
        ids = data.identifiers
        variables = {
            "company_name": "Glam You Up",
            "company_address": "31 Continental Dr, Suite 305, Newark, Delaware 19713, United States",
            "brand_color": "#BD4267",   # brand-700
            "domain": ids.domain,
            "platform_name": ids.platform_name,
            "platform_shop_id": ids.platform_shop_id,
            "merchant_id": str(ids.merchant_id),
            "current_year": datetime.now().year,
            "support_email": "support@glamyouup.com",
            "app_url": "https://app.glamyouup.com",
        }
        variables.update(data.model_dump(exclude={"identifiers"}))

        # Event-specific enrichment
        if event_type == "evt.merchant.created.v1" and hasattr(data, "shop_name"):
            variables["shop_name"] = data.shop_name or ids.domain

        if event_type == "evt.credit.low_balance.v1" and hasattr(data, "balance"):
            variables["balance"] = data.balance

        return variables

    async def get_notification(self, notification_id: UUID) -> NotificationOut:
        """Get notification by ID."""
        notification = await self.repository.find_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification not found", details={"notification_id": str(notification_id)})
        return notification

    async def list_notifications(
        self,
        filters: dict[str, Any] = None,
        skip: int = 0,
        limit: int = 50,
        order_by: list[tuple] = None,
    ) -> tuple[int, list[NotificationOut]]:
        """List notifications with filters."""
        total = await self.repository.count(filters=filters)
        notifications = await self.repository.find_many(
            filters=filters, skip=skip, limit=limit, order_by=order_by or [("first_attempt_at", "desc")]
        )
        return total, notifications

    async def get_stats(self) -> NotificationStats:
        """Get notification statistics."""
        return await self.repository.get_stats()

    async def get_health_metrics(self) -> dict:
        """Get system health metrics based on attempt distribution."""
        total_sent = await self.repository.count({"status": NotificationStatus.SENT})
        if total_sent == 0:
            return {
                "first_attempt_success_rate": 0,
                "avg_attempts": 0,
                "failure_rate": 0,
            }

        first_attempt_success = await self.repository.count({"status": NotificationStatus.SENT, "attempt_count": 1})

        total_notifications = await self.repository.count({})
        total_failed = await self.repository.count({"status": NotificationStatus.FAILED})

        return {
            "first_attempt_success_rate": round((first_attempt_success / total_sent) * 100, 2),
            "failure_rate": round((total_failed / total_notifications) * 100, 2) if total_notifications > 0 else 0,
            "total_sent": total_sent,
            "total_failed": total_failed,
        }
