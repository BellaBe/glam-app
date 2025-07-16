# services/notification-service/src/events/subscribers.py
"""Notification Service event subscribers"""

from shared.events.base_subscriber import DomainEventSubscriber
from shared.events.notification.types import NotificationCommands, SendEmailCommandPayload, SendEmailBulkCommandPayload

class SendEmailSubscriber(DomainEventSubscriber):
    """Single email send subscriber"""
    
    @property
    def event_type(self) -> str:
        return NotificationCommands.NOTIFICATION_SEND_EMAIL  # ✅ Correct override

    @property
    def subject(self) -> str:
        return NotificationCommands.NOTIFICATION_SEND_EMAIL
    @property
    def durable_name(self) -> str:
        return "notification-send-email"

    async def on_event(self, event: dict, headers=None):
        # Type-safe dependency access - IDE autocompletes valid keys
        notification_service = self.get_dependency("notification_service")
        
        payload = SendEmailCommandPayload(**event["payload"])
        await notification_service.process_send_email_command(payload)

class SendBulkEmailSubscriber(DomainEventSubscriber):
    """Bulk email send subscriber"""

    @property
    def event_type(self)-> str:
        return NotificationCommands.NOTIFICATION_SEND_BULK
    
    @property
    def subject(self) -> str:
        return NotificationCommands.NOTIFICATION_SEND_BULK
    
    @property
    def durable_name(self) -> str:
        return "notification-send-bulk"
    
    async def on_event(self, event: dict, headers=None):
        notification_service = self.get_dependency("notification_service")
        
        payload = SendEmailBulkCommandPayload(**event["payload"])
        await notification_service.process_bulk_email_command(payload)