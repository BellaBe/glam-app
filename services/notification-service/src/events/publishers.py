# services/notification-service/src/events/publishers.py
from shared.api.correlation import get_correlation_context
from shared.messaging.publisher import Publisher

from ..schemas.events import EmailFailedPayload, EmailSentPayload
from ..schemas.notification import NotificationOut


class NotificationEventPublisher(Publisher):
    """Publisher for notification events"""

    @property
    def service_name(self) -> str:
        return "notification-service"

    async def email_sent(self, notification: NotificationOut) -> str:
        """Publish email sent event"""
        payload = EmailSentPayload(
            notification_id=notification.id,
            merchant_id=notification.merchant_id,
            platform_name=notification.platform_name,
            platform_shop_id=notification.platform_shop_id,
            shop_domain=notification.shop_domain,
            template_type=notification.template_type,
            sent_at=notification.sent_at or notification.created_at,
        )

        # Get correlation ID from context (set by listener)
        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.notification.email.sent.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
            metadata={
                "recipient_email": notification.recipient_email,
                "provider": notification.provider,
            },
        )

    async def email_failed(self, notification: NotificationOut, error: str) -> str:
        """Publish email failed event"""
        payload = EmailFailedPayload(
            notification_id=notification.id,
            merchant_id=notification.merchant_id,
            platform_name=notification.platform_name,
            platform_shop_id=notification.platform_shop_id,
            shop_domain=notification.shop_domain,
            template_type=notification.template_type,
            error=error,
            failed_at=notification.failed_at or notification.created_at,
        )

        # Get correlation ID from context
        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.notification.email.failed.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
            metadata={
                "recipient_email": notification.recipient_email,
                "retry_count": notification.retry_count,
                "trigger_event": notification.trigger_event,
            },
        )
