# shared/messaging/listener.py
"""Enhanced listener with automatic envelope unpacking and type safety."""

import asyncio
import contextlib
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, TypeVar

from nats.errors import TimeoutError as NATSTimeoutError
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from nats.js.errors import NotFoundError

from shared.api.correlation import set_correlation_context
from shared.utils.logger import ServiceLogger

from .events.base import BaseEventPayload
from .jetstream_client import JetStreamClient

T = TypeVar("T", bound=BaseEventPayload)


class Listener(ABC, Generic[T]):
    """
    Enhanced listener with type-safe payload handling.
    """

    stream_name: str = "GLAM_EVENTS"
    batch_size: int = 10
    ack_wait_sec: int = 30
    max_deliver: int = 3
    idle_sleep_sec: float = 0.05
    poll_window_sec: float = 2.0

    _task: asyncio.Task | None = None
    _running: bool = False
    _sub = None

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Service name for consumer identification."""
        ...

    @property
    @abstractmethod
    def subject(self) -> str:
        """NATS subject to listen to (evt.* or cmd.*)."""
        ...

    @property
    @abstractmethod
    def queue_group(self) -> str:
        """Queue group for load balancing."""
        ...

    @property
    @abstractmethod
    def payload_class(self) -> type[T]:
        """Payload class for type validation."""
        ...

    def __init__(self, js_client: JetStreamClient, logger: ServiceLogger) -> None:
        self._js = js_client.js
        self.logger = logger
        # Track delivery attempts for DLQ logic
        self._delivery_attempts: dict[str, int] = {}

    async def start(self) -> None:
        """Start listening for events."""
        await self._ensure_consumer()
        await self._create_subscription()
        self.logger.info("Listener started", extra={"subject": self.subject, "service": self.service_name})
        self._running = True
        self._task = asyncio.create_task(self._poll_loop(), name=f"{self.service_name}:{self.subject}")

    async def stop(self) -> None:
        """Stop listening gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._sub:
            await self._sub.unsubscribe()
        self.logger.info("Listener stopped", extra={"subject": self.subject, "service": self.service_name})

    @abstractmethod
    async def on_message(
        self, payload: T, event_id: str, correlation_id: str, source_service: str, timestamp: datetime
    ) -> None:
        """
        Process message with typed payload and metadata.

        Args:
            payload: Typed and validated payload
            event_id: Unique event ID
            correlation_id: Correlation ID for tracing
            source_service: Service that published the event
            timestamp: When the event was published
        """
        ...

    async def on_error(self, error: Exception, event_id: str, correlation_id: str, delivery_count: int) -> bool:
        """
        Handle processing errors.

        Returns:
            True to ACK (don't retry), False to NACK (retry)
        """
        self.logger.error(
            "Error processing message",
            extra={
                "subject": self.subject,
                "event_id": event_id,
                "correlation_id": correlation_id,
                "delivery_count": delivery_count,
                "error": str(error),
            },
        )

        # Default: retry until max_deliver
        return delivery_count >= self.max_deliver

    async def _ensure_consumer(self) -> None:
        """Ensure consumer exists for this listener."""
        durable = f"{self.service_name}-{self.queue_group}"

        try:
            await self._js.consumer_info(self.stream_name, durable)
            self.logger.debug("Consumer exists: %s", durable)
        except NotFoundError:
            cfg = ConsumerConfig(
                durable_name=durable,
                deliver_policy=DeliverPolicy.ALL,
                ack_policy=AckPolicy.EXPLICIT,
                max_deliver=self.max_deliver,
                max_ack_pending=self.batch_size * 5,
                filter_subject=self.subject,
                ack_wait=self.ack_wait_sec,
            )
            await self._js.add_consumer(self.stream_name, cfg)
            self.logger.info("Created consumer: %s", durable)

    async def _create_subscription(self) -> None:
        """Create pull subscription."""
        durable = f"{self.service_name}-{self.queue_group}"
        self._sub = await self._js.pull_subscribe(
            self.subject,
            durable=durable,
            stream=self.stream_name,
        )

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        try:
            while self._running:
                if not self._sub:
                    self.logger.error("Subscription not initialized")
                    await asyncio.sleep(1)
                    continue

                try:
                    msgs = await self._sub.fetch(
                        batch=self.batch_size,
                        timeout=self.poll_window_sec,
                    )
                except (TimeoutError, NATSTimeoutError):
                    # Normal: no messages available
                    await asyncio.sleep(self.idle_sleep_sec)
                    continue

                if not msgs:
                    await asyncio.sleep(self.idle_sleep_sec)
                    continue

                # Process batch
                for msg in msgs:
                    await self._process_message(msg)

        except asyncio.CancelledError:
            self.logger.info("Poll loop cancelled")
        except Exception:
            self.logger.critical("Poll loop crashed", exc_info=True)

    async def _process_message(self, msg) -> None:
        """Process a single message with envelope unpacking."""
        delivery_count = 1

        try:
            # Get delivery count from metadata
            md = getattr(msg, "metadata", None)
            if md:
                delivery_count = getattr(md, "num_delivered", 1)

            # Parse the JSON envelope
            try:
                envelope_data = json.loads(msg.data.decode("utf-8"))
            except json.JSONDecodeError as e:
                self.logger.error("Failed to parse message JSON", extra={"error": str(e)})
                await msg.ack()  # ACK corrupt messages
                return

            # Extract envelope fields
            event_id = envelope_data.get("event_id")
            event_type = envelope_data.get("event_type")
            correlation_id = envelope_data.get("correlation_id")
            source_service = envelope_data.get("source_service")
            timestamp_str = envelope_data.get("timestamp")
            data = envelope_data.get("data")

            # Validate required fields
            if not all([event_id, event_type, correlation_id, source_service, timestamp_str, data]):
                self.logger.error("Missing required envelope fields", extra={"envelope": envelope_data})
                await msg.ack()
                return

            # Validate event type matches subject
            if event_type != self.subject:
                self.logger.warning(
                    "Subject mismatch", extra={"expected": self.subject, "received": event_type, "event_id": event_id}
                )
                await msg.ack()
                return

            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                timestamp = datetime.utcnow()

            # Validate and parse payload
            try:
                typed_payload = self.payload_class.model_validate(data)
            except Exception as e:
                self.logger.error(
                    "Payload validation failed", extra={"event_id": event_id, "error": str(e), "data": data}
                )
                await msg.ack()
                return

            # Set correlation context
            set_correlation_context(correlation_id)

            # Process message
            try:
                await self.on_message(typed_payload, event_id, correlation_id, source_service, timestamp)
                await msg.ack()

                # Clear delivery tracking on success
                if event_id in self._delivery_attempts:
                    del self._delivery_attempts[event_id]

            except Exception as e:
                # Track delivery attempts
                self._delivery_attempts[event_id] = delivery_count

                # Let subclass decide on retry strategy
                should_ack = await self.on_error(e, event_id, correlation_id, delivery_count)

                if should_ack:
                    await msg.ack()
                    if event_id in self._delivery_attempts:
                        del self._delivery_attempts[event_id]
                else:
                    await msg.nak()

        except Exception as e:
            self.logger.critical("Message processing failed catastrophically", extra={"error": str(e)}, exc_info=True)
            await msg.ack()
