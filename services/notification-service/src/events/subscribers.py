# services/notification-service/src/events/subscribers.py
from typing import Optional, Dict
from pydantic import ValidationError
from shared.events.base_subscriber import DomainEventSubscriber
from shared.events.notification.types import (
    NotificationCommands,
    SendEmailCommandPayload,
    SendEmailBulkCommandPayload
)
from shared.api.correlation import CorrelationContext
from contextlib import nullcontext
from ..services.notification_service import NotificationService


class SendEmailSubscriber(DomainEventSubscriber):
    """Handle single email send commands"""
    
    @property
    def event_type(self):
        return NotificationCommands.NOTIFICATION_SEND_EMAIL
    
    @property
    def subject(self):
        return NotificationCommands.NOTIFICATION_SEND_EMAIL
    
    @property
    def durable_name(self):
        return "notification-send-email"
    
    def __init__(self, client, js, notification_service: NotificationService, logger=None):
        super().__init__(client, js, logger)
        self.notification_service = notification_service
    
    async def on_event(self, event: dict, headers: Optional[Dict[str, str]] = None):
        """Process send email command"""
        correlation_id = event.get('correlation_id')
        try:
            # Extract from event envelope
            payload_data = event.get('payload', {})
            
            event_metadata = event.get('metadata', {})
            
            # Validate payload
            payload = SendEmailCommandPayload(**payload_data)
            
            self.logger.info(
                f"Processing email command",
                extra={
                    "correlation_id": correlation_id,
                    "notification_type": payload.notification_type,
                    "recipient": payload.recipient.email,
                    "source_service": event_metadata.get('source_service'),
                    "idempotency_key": event.get('idempotency_key')
                }
            )
            
            # Set correlation context
            async with CorrelationContext(correlation_id) if correlation_id else nullcontext():
                # Send notification - service handles its own database session
                await self.notification_service.send_notification(
                    shop_id=payload.recipient.shop_id,
                    shop_domain=payload.recipient.shop_domain,
                    recipient_email=payload.recipient.email,
                    notification_type=payload.notification_type,
                    dynamic_content=payload.recipient.dynamic_content,
                    correlation_id=correlation_id
                )
                    
        except ValidationError as e:
            self.logger.error(
                f"Invalid payload structure: {e}",
                extra={"event_id": event.get('event_id')}
            )
            return True  # Ack to prevent poison message
            
        except Exception as e:
            self.logger.error(
                f"Failed to process email command: {e}",
                extra={
                    "event_id": event.get('event_id'),
                    "correlation_id": correlation_id
                }
            )
            raise


class SendBulkEmailSubscriber(DomainEventSubscriber):
    """Handle bulk email send commands"""
    
    @property
    def event_type(self):
        return NotificationCommands.NOTIFICATION_SEND_BULK
    
    @property
    def subject(self):
        return NotificationCommands.NOTIFICATION_SEND_BULK
    
    @property
    def durable_name(self):
        return "notification-send-bulk"
    
    def __init__(self, client, js, notification_service: NotificationService, logger=None):
        super().__init__(client, js, logger)
        self.notification_service = notification_service
    
    async def on_event(self, event: dict, headers: Optional[Dict[str, str]] = None):
        """Process bulk email command"""
        correlation_id = event.get('correlation_id')
        try:
            # Extract from event envelope
            payload_data = event.get('payload', {})
            
            event_metadata = event.get('metadata', {})
            
            # Validate payload
            payload = SendEmailBulkCommandPayload(**payload_data)
            
            self.logger.info(
                f"Processing bulk email command",
                extra={
                    "correlation_id": correlation_id,
                    "notification_type": payload.notification_type,
                    "recipient_count": len(payload.recipients),
                    "source_service": event_metadata.get('source_service')
                }
            )
            
            async with CorrelationContext(correlation_id) if correlation_id else nullcontext():
                # Convert to format expected by service
                recipients = [
                    {
                        "shop_id": r.shop_id,
                        "shop_domain": r.shop_domain,
                        "email": r.email,
                        "dynamic_content": r.dynamic_content
                    }
                    for r in payload.recipients
                ]
                
                # Send bulk notifications - service handles database
                result = await self.notification_service.send_bulk_notifications(
                    notification_type=payload.notification_type,
                    recipients=recipients,
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    f"Bulk send completed",
                    extra={
                        "correlation_id": correlation_id,
                        "bulk_job_id": str(result["bulk_job_id"]),
                        "total_sent": result["total_sent"],
                        "total_failed": result["total_failed"]
                    }
                )
                    
        except ValidationError as e:
            self.logger.error(f"Invalid bulk payload structure: {e}")
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to process bulk email command: {e}",
                extra={"correlation_id": correlation_id}
            )
            raise