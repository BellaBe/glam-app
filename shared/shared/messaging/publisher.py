# shared/messaging/publisher.py
"""Enhanced publisher with standardized envelope and auto-correlation."""

from abc import ABC, abstractmethod
from typing import Any

from shared.utils.logger import ServiceLogger

from .events.base import EventEnvelope
from .jetstream_client import JetStreamClient


class Publisher(ABC):
    """Base publisher with standardized event publishing."""

    stream_name: str = "GLAM_EVENTS"  # Single stream for all events

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Service identifier for source tracking."""
        ...

    def __init__(self, jetstream_client: JetStreamClient, logger: ServiceLogger) -> None:
        self.js_client = jetstream_client
        self.logger = logger
        self._ensure_stream_created = False

    async def _ensure_stream(self) -> None:
        """Ensure GLAM_EVENTS stream exists (called once)."""
        if self._ensure_stream_created:
            return

        await self.js_client.ensure_stream(
            self.stream_name,
            subjects=["evt.>", "cmd.>", "dlq.>"],  # Prepared for DLQ
        )
        self._ensure_stream_created = True

    async def publish_event(
        self,
        subject: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> str:
        """
        Publish an event with automatic envelope wrapping.

        Args:
            subject: NATS subject (evt.* or cmd.*)
            payload: Typed event payload extending BaseEventPayload
            correlation_id: Optional - will use context if not provided
            metadata: Additional metadata

        Returns:
            event_id of the published event
        """

        if not (subject.startswith("evt.") or subject.startswith("cmd.") or subject.startswith("dlq.")):
            raise ValueError(f"Invalid subject pattern: {subject}. Must start with evt., cmd., or dlq.")

        envelope = EventEnvelope(
            event_type=subject,
            correlation_id=correlation_id,
            source_service=self.service_name,
            data=payload.model_dump(mode="json"),
        )

        # Set logging context for this publish operation
        self.logger.set_request_context(
            event_id=envelope.event_id,
            event_type=subject,
            correlation_id=correlation_id,
            service=self.service_name,
            entry_point="event_publisher"
        )

        try:
            self.logger.info("Publishing event")

            await self._ensure_stream()
            ack = await self.js_client.js.publish(subject, envelope.to_bytes())

            self.logger.info(
                "Event published successfully",
                extra={"sequence": ack.seq if ack else None}
            )

            return envelope.event_id

        except Exception as e:
            self.logger.exception(
                "Failed to publish event",
                extra={"error": str(e)}
            )
            raise
        finally:
            # Clear context after publishing
            self.logger.clear_request_context()

    async def publish_to_dlq(
        self,
        original_subject: str,
        error_payload: dict,
        correlation_id: str,
        error: Exception,
    ) -> str:
        """
        Publish failed event to dead letter queue.

        Args:
            original_subject: Original event subject that failed
            error_payload: Original payload that failed processing
            correlation_id: Original correlation ID
            error: The exception that occurred
        """
        # Convert subject to DLQ pattern: evt.order.created -> dlq.order.created
        dlq_subject = original_subject.replace("evt.", "dlq.").replace("cmd.", "dlq.")

        from .events.models import ErrorPayload

        error_data = ErrorPayload(
            error_code=type(error).__name__,
            error_message=str(error),
            failed_operation=original_subject,
            original_data=error_payload,
        )

        # Context will be set by publish_event
        return await self.publish_event(
            subject=dlq_subject,
            payload=error_data,
            correlation_id=correlation_id,
            metadata={"original_subject": original_subject},
        )