# services/notification-service/src/events/publishers.py
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from shared.events.base_publisher import DomainEventPublisher
from shared.events.types import Streams, Events
from shared.utils.logger import ServiceLogger

from src.models.database import NotificationType

logger = ServiceLogger(__name__)


class NotificationPublisher(DomainEventPublisher):
    """Publisher for notification domain events"""
    domain_stream = Streams.NOTIFICATIONS
    service_name_override = "notification-service"
    
    async def publish_email_sent(
        self,
        notification_id: UUID,
        shop_id: UUID,
        shop_domain: str,
        notification_type: NotificationType,
        to_email: str,
        subject: str,
        provider_message_id: str,
        correlation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish email sent event"""
        await self.publish_event_response(
            event_type=Events.NOTIFICATION_EMAIL_SENT,
            payload={
                "notification_id": str(notification_id),
                "shop_id": str(shop_id),
                "shop_domain": shop_domain,
                "type": notification_type.value,
                "to_email": to_email,
                "subject": subject,
                "provider_message_id": provider_message_id,
                "sent_at": datetime.utcnow().isoformat(),
            },
            correlation_id=correlation_id,
            metadata=metadata,
        )
        logger.info(f"Published email sent event for notification {notification_id}")
        
    async def publish_email_failed(
        self,
        notification_id: UUID,
        shop_id: UUID,
        shop_domain: str,
        notification_type: NotificationType,
        to_email: str,
        error_code: str,
        error_message: str,
        retry_count: int = 0,
        will_retry: bool = False,
        correlation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish email failed event"""
        await self.publish_event_response(
            event_type=Events.NOTIFICATION_EMAIL_FAILED,
            payload={
                "notification_id": str(notification_id),
                "shop_id": str(shop_id),
                "shop_domain": shop_domain,
                "type": notification_type.value,
                "to_email": to_email,
                "error_code": error_code,
                "error_message": error_message,
                "retry_count": retry_count,
                "will_retry": will_retry,
            },
            correlation_id=correlation_id,
            metadata=metadata,
        )
        logger.warning(f"Published email failed event for notification {notification_id}: {error_message}")
        
    async def publish_preferences_updated(
        self,
        shop_id: UUID,
        shop_domain: str,
        email_enabled: bool,
        notification_types: Dict[str, bool],
        timezone: str,
        correlation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish preferences updated event"""
        await self.publish_event_response(
            event_type=Events.NOTIFICATION_PREFERENCES_UPDATED,
            payload={
                "shop_id": str(shop_id),
                "shop_domain": shop_domain,
                "email_enabled": email_enabled,
                "notification_types": notification_types,
                "timezone": timezone,
                "updated_at": datetime.utcnow().isoformat(),
            },
            correlation_id=correlation_id,
            metadata=metadata,
        )
        logger.info(f"Published preferences updated event for shop {shop_id}")


class CatalogPublisher(DomainEventPublisher):
    """Publisher for cross-domain catalog events (used by notification service)"""
    domain_stream = Streams.CATALOG
    service_name_override = "notification-service"
    
    # This publisher can be used if notification service needs to publish
    # any catalog-related events (unlikely but possible for cross-domain communication)