# services/notification-service/src/events/publishers.py
from uuid import UUID

from shared.messaging.events.base import MerchantIdentifiers
from shared.messaging.publisher import Publisher

from ..schemas.events import EmailFailedPayload, NotificationSentPayload
from ..schemas.notification import NotificationOut


class NotificationEventPublisher(Publisher):
    """Publisher for notification events"""

    @property
    def service_name(self) -> str:
        return "notification-service"

    async def email_sent(self, notification: NotificationOut, ctx) -> str:
        """Publish email sent event"""

        identifiers = MerchantIdentifiers(
            merchant_id=UUID(notification.merchant_id),
            platform_name=notification.platform_name,
            platform_shop_id=notification.platform_shop_id,
            domain=notification.domain,
        )

        payload = NotificationSentPayload(
            identifiers=identifiers,
            notification_id=notification.id,
            template_type=notification.template_type,
            delivered_at=notification.delivered_at,
            provider=notification.provider_message.get("provider") if notification.provider_message else None,
        )

        return await self.publish_event(
            subject="evt.notification.email.sent.v1",
            payload=payload,
            correlation_id=ctx.correlation_id,
        )

    async def email_failed(self, notification: NotificationOut, error: str, ctx) -> str:
        """Publish email failed event"""
        payload = EmailFailedPayload(
            notification_id=notification.id,
            merchant_id=notification.merchant_id,
            platform_name=notification.platform_name,
            platform_shop_id=notification.platform_shop_id,
            domain=notification.domain,
            template_type=notification.template_type,
            error=error,
            failed_at=notification.failed_at or notification.created_at,
        )

        return await self.publish_event(
            subject="evt.notification.email.failed.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=ctx.correlation_id,
        )
