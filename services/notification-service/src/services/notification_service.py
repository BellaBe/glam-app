# services/notification-service/src/services/notification_service.py
from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID

from shared.utils import generate_idempotency_key
from shared.utils.exceptions import NotFoundError
from shared.utils.logger import ServiceLogger

from ..repositories.notification_repository import NotificationRepository
from ..schemas.notification import NotificationOut, NotificationStats
from .email_service import EmailService
from .template_service import TemplateService


class NotificationService:
    """Core notification business logic"""

    # Event to template mapping
    EVENT_TEMPLATE_MAP: ClassVar[dict[str, str]] = {
        "evt.merchant.created.v1": "welcome",
        "evt.credit.balance.low.v1": "credit_warning",
        "evt.credit.balance.depleted.v1": "zero_balance",
    }

    def __init__(
        self,
        repository: NotificationRepository,
        template_service: TemplateService,
        email_service: EmailService,
        logger: ServiceLogger,
        max_retries: int = 3,
    ):
        self.repository = repository
        self.template_service = template_service
        self.email_service = email_service
        self.logger = logger
        self.max_retries = max_retries

    def determine_template_type(self, event_type: str, event_data: dict[str, Any]) -> str | None:
        """Determine template type based on event"""
        # Special handling for catalog sync
        if event_type == "evt.catalog.sync.completed":
            if event_data.get("first_sync"):
                return "registration_complete"
            elif event_data.get("has_changes"):
                return "registration_update"
            return None

        # Standard mapping
        return self.EVENT_TEMPLATE_MAP.get(event_type)

    def generate_idempotency_key_for_event(self, event_type: str, event_data: dict[str, Any]) -> str:
        """Generate idempotency key for an event"""
        merchant_id = event_data.get("merchant_id", "unknown")
        event_id = event_data.get("correlation_id", "unknown")

        return generate_idempotency_key(
            system="NOTIFICATION",
            operation_type=event_type.replace(".", "_").upper(),
            identifier=merchant_id,
            extra=event_id,
        )

    async def process_event(
        self, event_type: str, event_data: dict[str, Any], correlation_id: str
    ) -> NotificationOut | None:
        """
        Process an event and send notification if needed

        Returns:
            NotificationOut if sent, None if skipped
        """
        # Generate idempotency key
        idempotency_key = self.generate_idempotency_key_for_event(event_type, event_data)

        # Check if already processed
        existing = await self.repository.find_by_idempotency_key(idempotency_key)
        if existing:
            self.logger.info(
                "Notification already processed",
                extra={
                    "idempotency_key": idempotency_key,
                    "notification_id": str(existing.id),
                    "correlation_id": correlation_id,
                },
            )
            return existing

        # Determine template type
        template_type = self.determine_template_type(event_type, event_data)
        if not template_type:
            self.logger.info(
                "No template for event",
                extra={"event_type": event_type, "correlation_id": correlation_id},
            )
            return None

        # Extract recipient email
        recipient_email = event_data.get("email")
        if not recipient_email:
            # Try to get from merchant service if needed
            self.logger.warning(
                "No email in event data",
                extra={"event_type": event_type, "correlation_id": correlation_id},
            )
            return None

        # Prepare template context
        context = self._prepare_template_context(event_data)

        # Render email
        try:
            subject, html_body, text_body = self.template_service.render_email(template_type, context)
        except NotFoundError:
            self.logger.error(
                f"Template not found: {template_type}",
                extra={"correlation_id": correlation_id},
            )
            # Store failed notification
            return await self._store_failed_notification(
                event_type=event_type,
                event_data=event_data,
                template_type=template_type,
                recipient_email=recipient_email,
                error="Template not found",
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )
        except Exception as e:
            self.logger.error(
                f"Template rendering failed: {e!s}",
                extra={"correlation_id": correlation_id},
            )
            return await self._store_failed_notification(
                event_type=event_type,
                event_data=event_data,
                template_type=template_type,
                recipient_email=recipient_email,
                error=str(e),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )

        # Send email
        try:
            provider_message_id = await self.email_service.send(
                to=recipient_email,
                subject=subject,
                html=html_body,
                text=text_body,
                metadata={
                    "merchant_id": str(event_data.get("merchant_id")),
                    "template_type": template_type,
                    "correlation_id": correlation_id,
                },
            )

            # Store successful notification
            notification = await self.repository.create(
                {
                    "merchant_id": str(event_data.get("merchant_id")),
                    "platform_name": event_data.get("platform_name"),
                    "platform_shop_id": event_data.get("platform_shop_id"),
                    "shop_domain": event_data.get("shop_domain"),
                    "recipient_email": recipient_email,
                    "template_type": template_type,
                    "subject": subject,
                    "status": "sent",
                    "provider": self.email_service.provider_name,
                    "provider_message_id": provider_message_id,
                    "trigger_event": event_type,
                    "trigger_event_id": correlation_id,
                    "idempotency_key": idempotency_key,
                    "template_variables": context,
                    "sent_at": datetime.utcnow(),
                }
            )

            self.logger.info(
                "Notification sent successfully",
                extra={
                    "notification_id": str(notification.id),
                    "template_type": template_type,
                    "correlation_id": correlation_id,
                },
            )

            return notification

        except Exception as e:
            self.logger.error(f"Email send failed: {e!s}", extra={"correlation_id": correlation_id})
            return await self._store_failed_notification(
                event_type=event_type,
                event_data=event_data,
                template_type=template_type,
                recipient_email=recipient_email,
                error=str(e),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )

    def _prepare_template_context(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare context for template rendering"""
        context = {
            "merchant_id": event_data.get("merchant_id"),
            "platform_name": event_data.get("platform_name"),
            "platform_shop_id": event_data.get("platform_shop_id"),
            "shop_domain": event_data.get("shop_domain"),
            "shop_domain": event_data.get("shop_domain"),  # Alias
            "shop_name": event_data.get("shop_name", event_data.get("shop_domain")),
            "current_year": datetime.now().year,
            "support_email": "support@glamyouup.com",
            "app_url": "https://app.glamyouup.com",
        }

        # Add all event data
        context.update(event_data)

        return context

    async def _store_failed_notification(
        self,
        event_type: str,
        event_data: dict[str, Any],
        template_type: str,
        recipient_email: str,
        error: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> NotificationOut:
        """Store a failed notification record"""
        notification = await self.repository.create(
            {
                "merchant_id": str(event_data.get("merchant_id")),
                "platform_name": event_data.get("platform_name"),
                "platform_shop_id": event_data.get("platform_shop_id"),
                "shop_domain": event_data.get("shop_domain"),
                "recipient_email": recipient_email,
                "template_type": template_type,
                "subject": "",  # No subject for failed
                "status": "failed",
                "error_message": error,
                "trigger_event": event_type,
                "trigger_event_id": correlation_id,
                "idempotency_key": idempotency_key,
                "template_variables": event_data,
                "failed_at": datetime.utcnow(),
            }
        )

        return notification

    async def get_notification(self, notification_id: UUID) -> NotificationOut:
        """Get notification by ID"""
        notification = await self.repository.find_by_id(notification_id)
        if not notification:
            raise NotFoundError(
                f"Notification {notification_id} not found",
                resource="notification",
                resource_id=str(notification_id),
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
