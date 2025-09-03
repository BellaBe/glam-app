# services/notification-service/src/services/notification_delivery_service.py
from uuid import UUID

from shared.utils.exceptions import NotFoundError
from shared.utils.logger import ServiceLogger

from ..repositories.notification_repository import NotificationRepository
from ..schemas.notification import AttemptStatus, NotificationStatus
from .email_service import EmailService
from .template_service import TemplateService


class NotificationDeliveryService:
    """
    Handles the actual delivery of notifications.
    Single responsibility: Send emails and track delivery attempts.
    """

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

    async def deliver_notification(self, notification_id: UUID) -> bool:
        """
        Deliver a notification and record the attempt.
        Returns True if successful, False otherwise.
        """
        notification = await self.repository.find_by_id(notification_id)
        if not notification:
            raise NotFoundError(
                f"Notification {notification_id} not found", resource="notification", resource_id=str(notification_id)
            )

        # Don't re-send already sent notifications
        if notification.status == NotificationStatus.SENT:
            self.logger.warning("Notification already sent", extra={"notification_id": str(notification_id)})
            return True

        # Get attempt number
        attempt_number = await self.repository.get_attempt_count(notification_id) + 1

        try:
            # Render template
            subject, html_body, text_body = self.template_service.render_email(
                notification.template_type, notification.template_variables
            )

            # Send email
            provider_message_id = await self.email_service.send(
                to=notification.recipient_email,
                subject=subject,
                html=html_body,
                text=text_body,
                metadata={
                    "notification_id": str(notification.id),
                    "merchant_id": notification.merchant_id,
                    "attempt": attempt_number,
                },
            )

            # Record successful attempt
            await self.repository.create_attempt(
                {
                    "notification_id": str(notification_id),
                    "attempt_number": attempt_number,
                    "provider": self.email_service.provider_name,
                    "status": AttemptStatus.SUCCESS,
                    "provider_response": {"message_id": provider_message_id},
                }
            )

            # Update notification status
            await self.repository.update(
                notification_id,
                {
                    "status": NotificationStatus.SENT,
                    "provider_message_id": provider_message_id,
                },
            )

            self.logger.info(
                "Notification delivered successfully",
                extra={
                    "notification_id": str(notification_id),
                    "provider_message_id": provider_message_id,
                    "attempt": attempt_number,
                },
            )

            return True

        except Exception as e:
            # Record failed attempt
            await self.repository.create_attempt(
                {
                    "notification_id": str(notification_id),
                    "attempt_number": attempt_number,
                    "provider": self.email_service.provider_name,
                    "status": AttemptStatus.FAILED,
                    "error_message": str(e),
                }
            )

            # Update notification status
            await self.repository.update(notification_id, {"status": NotificationStatus.FAILED})

            self.logger.error(
                f"Notification delivery failed: {e}",
                extra={"notification_id": str(notification_id), "attempt": attempt_number},
            )

            return False

    async def retry_failed_notifications(self, max_attempts: int = 3) -> int:
        """
        Retry failed notifications that haven't exceeded max attempts.
        Returns count of retried notifications.
        """
        failed_notifications = await self.repository.find_retriable_notifications(max_attempts)
        retry_count = 0

        for notification in failed_notifications:
            success = await self.deliver_notification(notification.id)
            if success:
                retry_count += 1

        return retry_count
