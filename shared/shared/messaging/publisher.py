# shared/messaging/publisher.py
"""Publisher base class for domain events and commands."""
import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from uuid import uuid4

from shared.utils.logger import ServiceLogger

from .jetstream_client import JetStreamClient


class Publisher(ABC):
    """Publishes domain facts (evt.*) and commands (cmd.*)"""

    @property
    @abstractmethod
    def service_name(self) -> str:
        ...

    def __init__(self, jetstream_client: JetStreamClient, logger: ServiceLogger) -> None:
        self.js_client = jetstream_client
        self.logger = logger

    async def publish_event(
        self,
        subject: str,
        data: dict,
        correlation_id: str,
        metadata: dict[str, dict] | None = None,
    ) -> str:
        """Publish an event to JetStream"""

        self.logger.info("Publishing event %s", subject)

        if not (subject.startswith("evt.") or subject.startswith("cmd.")):
            raise ValueError("subject must start with 'evt.' or 'cmd.'")

        event_id = str(uuid4())

        envelope = {
            "event_id": event_id,
            "event_type": subject,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "source_service": self.service_name,
            "data": data,
            "metadata": metadata or {},
        }

        try:
            # Publish directly - stream already exists
            ack = await self.js_client.js.publish(subject, json.dumps(envelope).encode())

            self.logger.info("Published %s [event_id=%s, seq=%s]", subject, event_id, ack.seq if ack else "unknown")
            return event_id

        except Exception as e:
            self.logger.error("Failed to publish event %s: %s", subject, str(e), exc_info=True)
            raise
