# services/notification-service/src/events/publishers.py

from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects
from shared.messaging.payloads.notification import (
    EmailSendComplete,
    EmailSendFailed,
    EmailSendBulkComplete
)


class EmailSendPublisher(Publisher):

    """Publisher for email send events in the notification service."""
    # ────────────────────────────────────────────────────────────────────────
    @property
    def service_name(self) -> str:
        """Returns the name of the service."""
        return "notification-service"


    async def email_send_complete(self, payload: EmailSendComplete, *, cid: str | None = None) -> str:
        """Publishes an email sent event."""
        subject = Subjects.EMAIL_SEND_COMPLETE
        return await self.publish_event(
            subject=subject.value,
            data=payload.model_dump(),
            correlation_id=cid,
        )

    async def email_send_failed(self, payload: EmailSendFailed, *, cid: str | None = None) -> str:
        """Publishes an email send failed event."""
        subject = Subjects.EMAIL_SEND_FAILED
        return await self.publish_event(
            subject=subject.value,
            data=payload.model_dump(),
            correlation_id=cid,
        )

    async def email_send_bulk_complete(self, payload: EmailSendBulkComplete, *, cid: str | None = None) -> str:
        """Publishes a bulk email send complete event."""
        subject = Subjects.EMAIL_SEND_BULK_COMPLETE
        return await self.publish_event(
            subject=subject.value,
            data=payload.model_dump(),
            correlation_id=cid,
        )
    