# services/notification_service/src/events/subscribers.py
from datetime import datetime
from shared.messaging.listener import Listener
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from ..services.notification_service import NotificationService
from .publishers import EmailSendPublisher
from shared.messaging.payloads.notification import (
    EmailSendRequested,
    EmailSendBulkRequested,
    EmailSendComplete,
    EmailSendFailed,
    EmailSendBulkComplete,
    EmailSendBulkFailed
)
from shared.messaging.subjects import Subjects
from ..schemas.notification import NotificationCreate


class SendEmailListener(Listener):
    
    @property
    def subject(self) -> str:
        return Subjects.EMAIL_SEND_REQUESTED
    
    @property
    def queue_group(self) -> str:
        return "notification-send"
    
    @property
    def service_name(self) -> str:
        return "notification-service"
    

    def __init__(
        self,
        js_client: JetStreamClient,
        publisher: EmailSendPublisher,
        svc: NotificationService,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.svc = svc
        self.pub = publisher

    async def on_message(self, data: dict) -> None:
        payload = EmailSendRequested(**data)  # validate & type
        
        try:
            out = await self.svc.create_and_send_notification(
                NotificationCreate(
                    merchant_id=payload.merchant_id,
                    merchant_domain=payload.merchant_domain,
                    notification_type=payload.email_type,
                    recipient_email=payload.recipient_email,
                    extra_metadata=payload.extra_metadata if payload.extra_metadata else {},
                )
            )
            
            # TODO: add provider info to svc return
            provider = "default_provider"  # Replace with actual provider logic
            provider_message_id = "12345"  # Replace with actual provider message ID
            sent_at = "2023-10-01T12:00:00Z"  # Replace with actual send_at timestamp

            await self.pub.email_send_complete(
                EmailSendComplete(
                    notification_id=out,
                    merchant_id=payload.merchant_id,
                    email_type=payload.email_type,
                    recipient_email=payload.recipient_email,
                    provider=provider,
                    provider_message_id=provider_message_id,
                    sent_at=datetime.fromisoformat(sent_at)
                ),
            )
        except Exception as exc:
            self.logger.error("Failed to send email: %s", exc)
            
            email_failed_payload = EmailSendFailed(
                notification_id=None,  # or the actual notification ID if available
                merchant_id=payload.merchant_id,
                template_name=payload.email_type,
                recipient_email=payload.recipient_email,
                error_message=str(exc),
                error_code="EMAIL_SEND_FAILED",
                retry_count=0,
                will_retry=False
            )

            await self.pub.email_send_failed(email_failed_payload)
            raise  # -> NACK, retry


class SendBulkEmailListener(Listener):
    
    @property
    def subject(self) -> str:
        return Subjects.EMAIL_SEND_BULK_REQUESTED
    
    @property
    def queue_group(self) -> str:
        return "notification-send"
    
    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(self, js_client: JetStreamClient, logger: ServiceLogger, svc: NotificationService, publisher: EmailSendPublisher):
        super().__init__(js_client, logger)
        self.svc = svc
        self.pub = publisher

    async def on_message(self, data: dict) -> None:
        payload = EmailSendBulkRequested(**data)
        
        # TODO: Implement bulk email sending logic