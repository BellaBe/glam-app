## File: services/notification-service/src/events/subscribers.py

from typing import Optional, Dict
from shared.events.base_subscriber import DomainEventSubscriber
from shared.events.types import Commands
from shared.api.correlation import CorrelationContext, extract_correlation_from_event
from shared.database import get_database_manager
from contextlib import nullcontext
from ..services.notification_service import NotificationService
from ..schemas.requests import NotificationCreate, BulkNotificationCreate

# Module-level storage for dependencies
_notification_service: Optional[NotificationService] = None

def set_notification_service(service: NotificationService):
    """Set the notification service for subscribers"""
    global _notification_service
    _notification_service = service

class SendEmailSubscriber(DomainEventSubscriber):
    """Handle single email send commands"""
    @property
    def event_type(self):
        return Commands.NOTIFICATION_SEND_EMAIL
    
    @property
    def subject(self):
        return Commands.NOTIFICATION_SEND_EMAIL
    
    @property
    def durable_name(self):
        """Durable name for this subscriber"""
        return "notification-send-email"
    
    async def on_event(self, event: dict, headers: Optional[Dict[str, str]] = None):
        """Process send email command with correlation context"""
        if not _notification_service:
            raise RuntimeError("Notification service not initialized")
            
        payload = event.get('payload', {})
        
        # Extract correlation ID from event
        correlation_id = extract_correlation_from_event(event)
        
        async with CorrelationContext(correlation_id) if correlation_id else nullcontext():
            try:
                # Get database manager from shared
                db_manager = get_database_manager()
                if not db_manager:
                    raise RuntimeError("Database manager not initialized")
                
                # Get a database session for this request
                async with db_manager.session() as session:
                    # Create notification request
                    notification_data = NotificationCreate(
                        shop_id=payload['shop_id'],
                        shop_domain=payload['shop_domain'],
                        recipient_email=payload['recipient_email'],
                        notification_type=payload['notification_type'],
                        template_id=payload.get('template_id'),
                        dynamic_content=payload.get('dynamic_content', {}),
                        metadata=payload.get('metadata', {})
                    )
                    
                    # Send notification
                    await _notification_service.send_notification(
                        notification_data,
                        session
                    )
                
            except Exception as e:
                self.logger.error(
                    f"Failed to process send email command: {e}",
                    extra={"correlation_id": correlation_id} if correlation_id else {}
                )
                raise

class SendBulkEmailSubscriber(DomainEventSubscriber):
    """Handle bulk email send commands"""
    @property
    def event_type(self):
        return Commands.NOTIFICATION_BULK_SEND
    
    @property
    def subject(self):
        return Commands.NOTIFICATION_BULK_SEND
    
    @property
    def durable_name(self):
        return "notification-send-bulk"
    
    async def on_event(self, event: dict, headers: Optional[Dict[str, str]] = None):
        """Process bulk email command with correlation context"""
        if not _notification_service:
            raise RuntimeError("Notification service not initialized")
            
        payload = event.get('payload', {})
        
        # Extract correlation ID from event
        correlation_id = extract_correlation_from_event(event)
        
        async with CorrelationContext(correlation_id) if correlation_id else nullcontext():
            try:
                # Get database manager from shared
                db_manager = get_database_manager()
                if not db_manager:
                    raise RuntimeError("Database manager not initialized")
                    
                # Get a database session for this request
                async with db_manager.session() as session:
                    # Create bulk notification request
                    bulk_data = BulkNotificationCreate(
                        template_id=payload['template_id'],
                        notification_type=payload['notification_type'],
                        recipients=payload['recipients']
                    )
                    
                    # Send notifications
                    await _notification_service.send_bulk_notifications(
                        bulk_data,
                        session
                    )
                
            except Exception as e:
                self.logger.error(
                    f"Failed to process bulk email command: {e}",
                    extra={"correlation_id": correlation_id} if correlation_id else {}
                )
                raise

def get_subscribers():
    """Get all subscribers for this service"""
    return [SendEmailSubscriber, SendBulkEmailSubscriber]