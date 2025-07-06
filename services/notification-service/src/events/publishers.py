# services/notification-service/src/events/publishers.py
from shared.events import Streams, DomainEventPublisher, EventContextManager, EventContext
from shared.events.base_publisher import DomainEventPublisher
from shared.events.notification.types import (
    NotificationEvents,
    EmailSentEventPayload,
    EmailFailedEventPayload,
    BulkCompletedEventPayload
)
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone


class NotificationEventPublisher(DomainEventPublisher):
    """Publisher for notification service events with standardized context"""
    domain_stream = Streams.NOTIFICATION
    service_name_override = "notification-service"
    
    def __init__(self, client, js, logger=None):
        super().__init__(client, js, logger)
        self.context_manager = EventContextManager(logger or self.logger)
    
    async def publish_email_sent(
        self,
        notification_id: UUID,
        shop_id: UUID,
        notification_type: str,
        provider: str,
        provider_message_id: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        original_event_id: Optional[str] = None
    ) -> str:
        """Publish email sent event with typed payload and context"""
        # Create event context
        context = EventContext(
            event_id=str(UUID()),
            event_type=NotificationEvents.NOTIFICATION_EMAIL_SENT,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override or "default-service-name",
            metadata={
                **(metadata or {}),
                "notification_id": str(notification_id),
                "triggered_by": original_event_id
            }
        )
        
        # Create typed payload
        payload = EmailSentEventPayload(
            notification_id=notification_id,
            shop_id=shop_id,
            notification_type=notification_type,
            provider=provider,
            provider_message_id=provider_message_id,
            sent_at=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        # Log event publication
        self.logger.info(
            f"Publishing {context.event_type}",
            extra=context.to_dict()
        )
        
        return await self.publish_event_response(
            NotificationEvents.NOTIFICATION_EMAIL_SENT,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=context.metadata
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
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        original_event_id: Optional[str] = None
    ) -> str:
        """Publish email failed event with typed payload and context"""
        # Create event context
        context = EventContext(
            event_id=str(UUID()),
            event_type=NotificationEvents.NOTIFICATION_EMAIL_FAILED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override or "default-service-name",
            metadata={
                **(metadata or {}),
                "notification_id": str(notification_id),
                "triggered_by": original_event_id,
                "will_retry": will_retry
            }
        )
        
        # Create typed payload
        payload = EmailFailedEventPayload(
            notification_id=notification_id,
            shop_id=shop_id,
            notification_type=notification_type,
            error=error,
            error_code=error_code,
            retry_count=retry_count,
            will_retry=will_retry,
            failed_at=datetime.now(timezone.utc)
        )
        
        # Log event publication
        self.logger.warning(
            f"Publishing {context.event_type}",
            extra={
                **context.to_dict(),
                "error": error,
                "error_code": error_code
            }
        )
        
        return await self.publish_event_response(
            NotificationEvents.NOTIFICATION_EMAIL_FAILED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=context.metadata
        )
    
    async def publish_bulk_completed(
        self,
        bulk_job_id: UUID,
        notification_type: str,
        total_recipients: int,
        total_sent: int,
        total_failed: int,
        total_skipped: int,
        duration_seconds: float,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        original_event_id: Optional[str] = None
    ) -> str:
        """Publish bulk send completed event with context"""
        # Create event context
        context = EventContext(
            event_id=str(UUID()),
            event_type=NotificationEvents.NOTIFICATION_BULK_SEND_COMPLETED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override or "default-service-name",
            idempotency_key=str(bulk_job_id),  # Use bulk job ID for idempotency
            metadata={
                **(metadata or {}),
                "bulk_job_id": str(bulk_job_id),
                "triggered_by": original_event_id,
                "success_rate": total_sent / total_recipients if total_recipients else 0
            }
        )
        
        # Create typed payload
        payload = BulkCompletedEventPayload(
            bulk_job_id=bulk_job_id,
            notification_type=notification_type,
            total_recipients=total_recipients,
            total_sent=total_sent,
            total_failed=total_failed,
            total_skipped=total_skipped,
            duration_seconds=duration_seconds,
            completed_at=datetime.now(timezone.utc)
        )
        
        # Log event publication
        self.logger.info(
            f"Publishing {context.event_type}",
            extra={
                **context.to_dict(),
                "total_sent": total_sent,
                "total_failed": total_failed,
                "duration_seconds": duration_seconds
            }
        )
        
        return await self.publish_event_response(
            NotificationEvents.NOTIFICATION_BULK_SEND_COMPLETED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=context.metadata
        )


def get_publishers():
    """Get all publishers for this service"""
    return [NotificationEventPublisher]