# services/notification-service/src/events/subscribers.py

"""Event subscribers for notification service with improved context handling."""

from typing import Optional, Dict, Any
from pydantic import ValidationError

from shared.events.base_subscriber import DomainEventSubscriber
from shared.events.notification.types import (
    NotificationCommands,
    SendEmailCommandPayload,
    SendEmailBulkCommandPayload
)
from shared.api.correlation import set_correlation_context, extract_correlation_from_event

from ..schemas import NotificationCreate
from ..services.notification_service import NotificationService


class NotificationEventSubscriber(DomainEventSubscriber):
    """Base class for notification event subscribers with context handling."""
    
    def __init__(
        self, 
        client, 
        js, 
        notification_service: NotificationService, 
        logger=None
    ):
        super().__init__(client, js, logger)
        self.notification_service = notification_service
    
    async def process_event(self, event: dict, headers: Optional[Dict[str, str]] = None):
        """Process event with proper context setup."""
        # Extract correlation ID from event
        correlation_id = extract_correlation_from_event(event)
        
        # Set correlation context for the entire request lifecycle
        if correlation_id:
            set_correlation_context(correlation_id)
        
        # Extract common metadata
        event_metadata = event.get('metadata', {})
        
        self.logger.info(
            f"Processing {self.event_type} event",
            extra={
                "event_id": event.get('event_id'),
                "event_type": self.event_type,
                "correlation_id": correlation_id,
                "source_service": event_metadata.get('source_service'),
                "idempotency_key": event.get('idempotency_key')
            }
        )
        
        try:
            # Delegate to specific handler
            await self.handle_event(event, correlation_id)
            
        except ValidationError as e:
            self.logger.error(
                f"Invalid payload structure: {e}",
                extra={
                    "event_id": event.get('event_id'),
                    "correlation_id": correlation_id,
                    "validation_errors": e.errors()
                }
            )
            # Return True to ACK and prevent poison message
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to process {self.event_type}: {str(e)}",
                extra={
                    "event_id": event.get('event_id'),
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            # Re-raise to trigger retry logic
            raise
    
    async def handle_event(self, event: dict, correlation_id: Optional[str]):
        """Override in subclasses to handle specific event logic."""
        raise NotImplementedError
    
    async def on_event(self, event: Dict[str, Any], headers: Optional[Dict[str, str]] = None): # type: ignore
        """Entry point for event processing."""
        return await self.process_event(event, headers)


class SendEmailSubscriber(NotificationEventSubscriber):
    """Handle single email send commands."""
    
    @property
    def event_type(self):
        return NotificationCommands.NOTIFICATION_SEND_EMAIL
    
    @property
    def subject(self):
        return NotificationCommands.NOTIFICATION_SEND_EMAIL
    
    @property
    def durable_name(self):
        return "notification-send-email"
    
    async def handle_event(self, event: dict, correlation_id: Optional[str]):
        """Process send email command."""
        # Extract and validate payload
        payload_data = event.get('payload', {})
        payload = SendEmailCommandPayload(**payload_data)
        
        self.logger.info(
            "Sending single notification",
            extra={
                "notification_type": payload.notification_type,
                "recipient": payload.recipient.email,
                "shop_id": str(payload.recipient.id),
                "correlation_id": correlation_id
            }
        )
        
        notification_create = NotificationCreate(
            notification_type=payload.notification_type,
            shop_id=payload.recipient.id,
            shop_domain=payload.recipient.domain,
            shop_email=payload.recipient.email,
            unsubscribe_token=payload.recipient.unsubscribe_token,
            dynamic_content=payload.recipient.dynamic_content or {},
            extra_metadata={
                    "source_event": self.event_type,
                    "event_id": event.get('event_id'),
                    "correlation_id": correlation_id
                }
        )
        
        # Create notification through service
        # The service will use the correlation context that we set
        notification = await self.notification_service.create_and_send_notification(notification_create)

        self.logger.info(
            "Notification sent successfully",
            extra={
                "notification_id": str(notification),
                "correlation_id": correlation_id
            }
        )


class SendBulkEmailSubscriber(NotificationEventSubscriber):
    """Handle bulk email send commands."""
    
    @property
    def event_type(self):
        return NotificationCommands.NOTIFICATION_SEND_BULK
    
    @property
    def subject(self):
        return NotificationCommands.NOTIFICATION_SEND_BULK
    
    @property
    def durable_name(self):
        return "notification-send-bulk"
    
    async def handle_event(self, event: dict, correlation_id: Optional[str]):
        """Process bulk email command."""
        # Extract and validate payload
        payload_data = event.get('payload', {})
        payload = SendEmailBulkCommandPayload(**payload_data)
        
        self.logger.info(
            "Processing bulk email send",
            extra={
                "notification_type": payload.notification_type,
                "recipient_count": len(payload.recipients),
                "correlation_id": correlation_id
            }
        )
        
        # Process in batches to avoid overwhelming the system
        batch_size = 50  # Configure based on your needs
        total_sent = 0
        total_failed = 0
        
        for i in range(0, len(payload.recipients), batch_size):
            batch = payload.recipients[i:i + batch_size]
            
            # Create notifications for this batch
            for recipient in batch:
                try:
                    notification_create = NotificationCreate(
                        shop_id=recipient.id,
                        shop_domain=recipient.domain,
                        shop_email=recipient.email,
                        unsubscribe_token=recipient.unsubscribe_token,
                        notification_type=payload.notification_type,
                        dynamic_content=recipient.dynamic_content or {},
                        extra_metadata={
                            "source_event": self.event_type,
                            "event_id": event.get('event_id'),
                            "correlation_id": correlation_id,
                            "bulk_batch": i // batch_size + 1
                        }
            )
                    await self.notification_service.create_and_send_notification(
                        notification_create
                    )
                    total_sent += 1
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to send to recipient: {str(e)}",
                        extra={
                            "recipient_email": recipient.email,
                            "correlation_id": correlation_id
                        }
                    )
                    total_failed += 1
        
        self.logger.info(
            "Bulk send completed",
            extra={
                "correlation_id": correlation_id,
                "total_sent": total_sent,
                "total_failed": total_failed,
                "total_recipients": len(payload.recipients)
            }
        )