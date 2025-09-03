# services/notification-service/src/services/notification_service.py
from datetime import datetime
from typing import ClassVar
from uuid import UUID

from shared.messaging.events.base import BaseEventPayload
from shared.utils import generate_idempotency_key
from shared.utils.exceptions import NotFoundError
from shared.utils.logger import ServiceLogger

from ..repositories.notification_repository import NotificationRepository
from ..schemas.notification import NotificationOut, NotificationStats, NotificationStatus


class NotificationService:
    """
    Core notification service - handles notification creation and tracking.
    Single responsibility: Record and manage notification state.
    """

    # Event to template mapping
    EVENT_TEMPLATE_MAP: ClassVar[dict[str, str]] = {
        "evt.merchant.created.v1": "welcome",
        "evt.credit.balance.low.v1": "credit_warning",
        "evt.credit.balance.depleted.v1": "zero_balance",
        "evt.catalog.sync.started.v1": "catalog_sync_started",
        "evt.catalog.sync.completed.v1": "catalog_sync_completed",
    }

    def __init__(
        self,
        repository: NotificationRepository,
        logger: ServiceLogger,
    ):
        self.repository = repository
        self.logger = logger

    def _determine_template_type(self, event_type: str, data: BaseEventPayload) -> str | None:
        """Determine template type based on event"""
        if event_type == "evt.catalog.sync.completed.v1":
            if hasattr(data, "first_sync") and data.first_sync:
                return "registration_complete"
            elif hasattr(data, "has_changes") and data.has_changes:
                return "registration_update"
            return None

        return self.EVENT_TEMPLATE_MAP.get(event_type)

    def _extract_recipient_email(self, data: BaseEventPayload) -> str | None:
        """Extract recipient email from event data"""
        if hasattr(data, "email"):
            return data.email
        # Future: Implement merchant service lookup
        return None

    def _prepare_template_variables(self, event_type: str, data: BaseEventPayload) -> dict:
        """Prepare template variables for storage"""
        platform_ctx = data.platform

        # Base context
        variables = {
            # Platform context (includes domain)
            "domain": platform_ctx.domain,
            "platform_name": platform_ctx.platform_name,
            "platform_shop_id": platform_ctx.platform_shop_id,
            # Global template variables
            "current_year": datetime.now().year,
            "support_email": "support@glamyouup.com",
            "app_url": "https://app.glamyouup.com",
        }

        # Add event-specific data (excluding platform)
        event_data = data.model_dump(exclude={"platform"})
        variables.update(event_data)

        # Event-specific enrichment
        if event_type == "evt.merchant.created.v1" and hasattr(data, "shop_name"):
            variables["shop_name"] = data.shop_name or platform_ctx.domain

        if event_type == "evt.credit.balance.low.v1" and hasattr(data, "balance"):
            variables["balance_percentage"] = round((data.balance / data.threshold) * 100, 1)

        return variables

    async def process_event(
        self,
        event_type: str,
        data: BaseEventPayload,
        event_id: str,
        correlation_id: str,
        delivery_service: "NotificationDeliveryService" = None,
    ) -> NotificationOut | None:
        """
        Process an event and create notification record.
        Optionally trigger immediate delivery via delivery service.
        """
        platform_ctx = data.platform

        # Generate idempotency key
        idempotency_key = generate_idempotency_key(platform_ctx.platform_name, "notification", event_id)

        # Check idempotency
        existing = await self.repository.find_by_idempotency_key(idempotency_key)
        if existing:
            self.logger.info(
                "Notification already processed",
                extra={
                    "idempotency_key": idempotency_key,
                    "notification_id": str(existing.id),
                },
            )
            return existing

        # Determine template
        template_type = self._determine_template_type(event_type, data)
        if not template_type:
            self.logger.info("No template for event", extra={"event_type": event_type})
            return None

        # Extract recipient
        recipient_email = self._extract_recipient_email(data)
        if not recipient_email:
            self.logger.warning(
                "No recipient email found",
                extra={"event_type": event_type, "merchant_id": str(platform_ctx.merchant_id)},
            )
            return None

        # Prepare template variables
        template_variables = self._prepare_template_variables(event_type, data)

        # Create notification record
        notification = await self.repository.create(
            {
                "merchant_id": str(platform_ctx.merchant_id),
                "platform_name": platform_ctx.platform_name,
                "platform_shop_id": platform_ctx.platform_shop_id,
                "recipient_email": recipient_email,
                "template_type": template_type,
                "status": NotificationStatus.PENDING,
                "trigger_event": event_type,
                "idempotency_key": idempotency_key,
                "template_variables": template_variables,  # Includes domain
            }
        )

        self.logger.info(
            "Notification created",
            extra={
                "notification_id": str(notification.id),
                "template_type": template_type,
            },
        )

        # Trigger delivery if service provided
        if delivery_service:
            await delivery_service.deliver_notification(notification.id)
            # Refresh to get updated status
            notification = await self.repository.find_by_id(notification.id)

        return notification

    async def get_notification(self, notification_id: UUID) -> NotificationOut:
        """Get notification by ID"""
        notification = await self.repository.find_by_id(notification_id)
        if not notification:
            raise NotFoundError(
                f"Notification {notification_id} not found", resource="notification", resource_id=str(notification_id)
            )
        return notification

    async def list_notifications(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        merchant_id: UUID | None = None,
    ) -> tuple[int, list[NotificationOut]]:
        """List notifications with filtering"""
        filters = {}
        if status:
            filters["status"] = status
        if merchant_id:
            filters["merchant_id"] = str(merchant_id)

        total = await self.repository.count(filters)
        notifications = await self.repository.find_many(
            filters=filters, skip=skip, limit=limit, order_by=[("created_at", "desc")]
        )

        return total, notifications

    async def get_stats(self) -> NotificationStats:
        """Get notification statistics"""
        return await self.repository.get_stats()
