# services/notification-service/src/events/publishers.py

from shared.events.base_publisher import DomainEventPublisher
from shared.events.types import Streams, Events
from shared.api.correlation import add_correlation_to_event
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from shared.events.base_publisher import DomainEventPublisher
from shared.events.types import Streams, Events
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

class NotificationPublisher(DomainEventPublisher):
    """Notification service event publisher"""
    domain_stream = Streams.NOTIFICATION
    service_name_override = "notification-service"
    
    async def publish_email_sent(
        self,
        notification_id: UUID,
        shop_id: UUID,
        notification_type: str,
        provider_message_id: str,
        correlation_id: Optional[str] = None
    ):
        """Publish email sent event"""
        await self.publish_event_response(
            Events.NOTIFICATION_EMAIL_SENT,
            {
                "notification_id": str(notification_id),
                "shop_id": str(shop_id),
                "notification_type": notification_type,
                "provider_message_id": provider_message_id,
                "sent_at": datetime.now(timezone.utc).isoformat()
            },
            correlation_id=correlation_id
        )
    
    async def publish_email_failed(
        self,
        notification_id: UUID,
        shop_id: UUID,
        notification_type: str,
        error: str,
        error_code: str,
        retry_count: int,
        will_retry: bool,
        correlation_id: Optional[str] = None
    ):
        """Publish email failed event"""
        await self.publish_event_response(
            Events.NOTIFICATION_DELIVERY_FAILED,
            {
                "notification_id": str(notification_id),
                "shop_id": str(shop_id),
                "notification_type": notification_type,
                "error": error,
                "error_code": error_code,
                "retry_count": retry_count,
                "will_retry": will_retry,
                "failed_at": datetime.now(timezone.utc).isoformat()
            },
            correlation_id=correlation_id
        )

def get_publishers():
    """Get all publishers for this service"""
    return [NotificationPublisher]