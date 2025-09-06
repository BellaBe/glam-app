# shared/messaging/listener.py
"""Simple listener using EventEnvelope directly."""

import asyncio
import contextlib
import json
from abc import ABC, abstractmethod

from nats.errors import TimeoutError as NATSTimeoutError
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from nats.js.errors import NotFoundError

from shared.utils.logger import ServiceLogger

from .events.base import EventEnvelope
from .jetstream_client import JetStreamClient


class Listener(ABC):
    """
    Base listener that passes EventEnvelope to subclasses.
    """

    stream_name: str = "GLAM_EVENTS"
    batch_size: int = 10
    max_deliver: int = 3
    idle_sleep_sec: float = 0.05
    poll_window_sec: float = 2.0

    @property
    @abstractmethod
    def service_name(self) -> str: ...

    @property
    @abstractmethod
    def subject(self) -> str: ...

    @property
    @abstractmethod
    def queue_group(self) -> str: ...

    def __init__(self, js_client: JetStreamClient, logger: ServiceLogger):
        self._js = js_client.js
        self.logger = logger
        self._sub = None
        self._task = None
        self._running = False

    async def start(self) -> None:
        """Start listening."""
        durable = f"{self.service_name}-{self.queue_group}"

        try:
            await self._js.consumer_info(self.stream_name, durable)
        except NotFoundError:
            await self._js.add_consumer(
                self.stream_name,
                ConsumerConfig(
                    durable_name=durable,
                    deliver_policy=DeliverPolicy.ALL,
                    ack_policy=AckPolicy.EXPLICIT,
                    max_deliver=self.max_deliver,
                    filter_subject=self.subject,
                ),
            )

        self._sub = await self._js.pull_subscribe(self.subject, durable=durable, stream=self.stream_name)

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        self.logger.info(f"Started listener: {self.subject}")

    async def stop(self) -> None:
        """Stop listening."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        if self._sub:
            await self._sub.unsubscribe()

    @abstractmethod
    async def on_message(self, envelope: EventEnvelope) -> None:
        """
        Handle message with EventEnvelope.
        Data field is not typed yet - subclass must validate.
        """
        ...

    async def _poll_loop(self) -> None:
        """Polling loop."""
        while self._running:
            try:
                msgs = await self._sub.fetch(batch=self.batch_size, timeout=self.poll_window_sec)
            except (TimeoutError, NATSTimeoutError):
                await asyncio.sleep(self.idle_sleep_sec)
                continue

            for msg in msgs:
                await self._handle_message(msg)

    async def _handle_message(self, msg) -> None:
        """Parse envelope and handle message."""
        try:
            # Parse into EventEnvelope (without typed data)
            envelope = EventEnvelope.model_validate_json(msg.data)

            # Process message
            try:
                await self.on_message(envelope)
                await msg.ack()

            except Exception as e:
                # Get delivery count
                delivery_count = 1
                if hasattr(msg, "metadata") and msg.metadata:
                    delivery_count = getattr(msg.metadata, "num_delivered", 1)

                if delivery_count >= self.max_deliver:
                    self.logger.error(
                        f"Max retries for {envelope.event_id}",
                        extra={
                            "error": str(e),
                            "event_type": envelope.event_type,
                            "correlation_id": envelope.correlation_id,
                        },
                    )
                    await msg.ack()  # Don't retry anymore
                else:
                    self.logger.error(
                        f"Error processing {envelope.event_id} (attempt {delivery_count})",
                        extra={
                            "error": str(e),
                            "event_type": envelope.event_type,
                            "correlation_id": envelope.correlation_id,
                        },
                    )
                    await msg.nak()  # Retry

        except json.JSONDecodeError:
            self.logger.error("Invalid JSON message")
            await msg.ack()
        except Exception as e:
            self.logger.error(f"Invalid envelope structure: {e}")
            await msg.ack()
