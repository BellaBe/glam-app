# shared/shared/messaging/publisher.py
"""Enhanced publisher with automatic enum handling and validation."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from shared.utils.logger import ServiceLogger

from .events.base import EventEnvelope
from .jetstream_client import JetStreamClient


class Publisher(ABC):
    """Base publisher with standardized event publishing."""

    stream_name: str = "GLAM_EVENTS"
    _stream_initialized: bool = False

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Service identifier for source tracking."""
        ...

    def __init__(self, jetstream_client: JetStreamClient, logger: ServiceLogger) -> None:
        self.js_client = jetstream_client
        self.logger = logger

    async def publish_event(
        self,
        subject: str | Enum,
        payload: Any,  # Should be a Pydantic model
        correlation_id: str,
    ) -> str:
        """
        Publish an event with automatic envelope wrapping.

        Args:
            subject: NATS subject (string or Enum with value)
            payload: Pydantic model that extends BaseEventPayload
            correlation_id: Request correlation ID

        Returns:
            event_id of the published event
        """
        # Handle Enum subjects automatically
        if isinstance(subject, Enum):
            subject = subject.value

        # Validate subject pattern
        if not any(subject.startswith(prefix) for prefix in ["evt.", "cmd.", "dlq."]):
            raise ValueError(f"Invalid subject '{subject}'. Must start with evt., cmd., or dlq.")

        # Convert Pydantic model to dict
        if hasattr(payload, "model_dump"):
            payload_dict = payload.model_dump(mode="json")
        else:
            payload_dict = payload

        # Create envelope
        envelope = EventEnvelope(
            event_type=subject,
            correlation_id=correlation_id,
            source_service=self.service_name,
            data=payload_dict,
        )

        # Set logging context
        self.logger.set_request_context(
            event_id=envelope.event_id,
            event_type=subject,
            correlation_id=correlation_id,
            service=self.service_name,
            entry_point="event_publisher",
        )

        try:
            # Ensure stream exists once per publisher instance
            if not Publisher._stream_initialized:
                await self.js_client.ensure_stream(
                    self.stream_name,
                    subjects=["evt.>", "cmd.>", "dlq.>"],
                )
                Publisher._stream_initialized = True

            # Publish with timeout
            ack = await self.js_client.js.publish(subject, envelope.to_bytes(), timeout=5.0)

            self.logger.info(
                f"Event published: {subject}",
                extra={"sequence": ack.seq if ack else None, "event_id": envelope.event_id},
            )

            return envelope.event_id

        except Exception as e:
            self.logger.exception(
                f"Failed to publish event to {subject}", extra={"error": str(e), "event_id": envelope.event_id}
            )
            raise
        finally:
            self.logger.clear_request_context()

    async def publish_to_dlq(
        self,
        original_event: EventEnvelope,
        error: str,
        correlation_id: str,
    ) -> str:
        """
        Publish an event to the Dead Letter Queue (DLQ).

        Args:
            original_event: The original event envelope that failed processing
            error: Description of the error that occurred
            correlation_id: Request correlation ID

        Returns:
            event_id of the DLQ event
        """
        dlq_subject = f"dlq.{original_event.event_type}"

        dlq_payload = {
            "original_event": original_event.model_dump(mode="json"),
            "error": error,
        }

        return await self.publish_event(
            subject=dlq_subject,
            payload=dlq_payload,
            correlation_id=correlation_id,
        )
