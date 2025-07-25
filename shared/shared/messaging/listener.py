# shared/messaging/js_listener.py
"""A thin, “safe” JetStream listener with JSON decode guard and error handling."""

import asyncio, json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from nats.js.errors import NotFoundError

from shared.utils.logger import ServiceLogger
from .jetstream_client import JetStreamClient
from .event_context import set_correlation_id, set_source_service


class Listener(ABC):
    """
    A thin, “safe” JetStream listener:
    • one subject
    • JSON decode guard
    • soft-fail vs. hard-fail error handling
    """
    
    stream_name: str = "GLAM_EVENTS"
    batch_size: int = 10
    ack_wait_sec: int = 30
    max_deliver: int = 3

    # ---- subclasses MUST fill these --------------------------------------
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Name of the owning micro-service (used for durable name)."""
        pass

    @property
    @abstractmethod
    def subject(self) -> str:
        """Full NATS subject to consume, e.g. ``evt.email.sent.v1``."""
        pass

    @property
    @abstractmethod
    def queue_group(self) -> str:
        """Queue group so replicas share the workload."""
        pass

    # ----------------------------------------------------------------------
    def __init__(self, js_client: JetStreamClient, logger: ServiceLogger) -> None:
        self._js = js_client.js
        self.logger = logger
        self._sub = None

    # ======================================================================
    # public API
    # ======================================================================
    async def start(self) -> None:
        await self._ensure_stream()
        await self._ensure_consumer()
        await self._create_subscription()
        self.logger.info("Listening on %s", self.subject)
        asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        if self._sub:
            await self._sub.unsubscribe()

    # ======================================================================
    # override in subclasses
    # ======================================================================
    @abstractmethod
    async def on_message(self, data: Dict[str, Any]) -> None: ...

    # ======================================================================
    # internals
    # ======================================================================
    # stream
    async def _ensure_stream(self) -> None:
        """Stream must exist and cover ``evt.*`` **and** ``cmd.*``."""
        from nats.js.api import RetentionPolicy, StorageType, StreamConfig  # local to avoid circulars

        try:
            await self._js.stream_info(self.stream_name)
        except NotFoundError:
            cfg = StreamConfig(
                name=self.stream_name,
                subjects=["evt.*", "cmd.*"],
                retention=RetentionPolicy.LIMITS,
                max_age=24 * 60 * 60,
                max_msgs=1_000_000,
                storage=StorageType.FILE,
            )
            await self._js.add_stream(cfg)
            self.logger.info("Created stream %s", self.stream_name)
        

    # consumer
    async def _ensure_consumer(self) -> None:
        durable = f"{self.service_name}-{self.queue_group}"
        try:
            await self._js.consumer_info(self.stream_name, durable)
        except NotFoundError:
            cfg = ConsumerConfig(
                durable_name=durable,
                deliver_policy=DeliverPolicy.ALL,
                ack_policy=AckPolicy.EXPLICIT,
                max_deliver=self.max_deliver,
                ack_wait=self.ack_wait_sec,
                filter_subject=self.subject,
            )
            await self._js.add_consumer(self.stream_name, cfg)

    # subscription
    async def _create_subscription(self) -> None:
        self._sub = await self._js.pull_subscribe(
            self.subject,
            durable=f"{self.service_name}-{self.queue_group}",
            stream=self.stream_name,
        )

    # polling loop
    async def _poll_loop(self) -> None:
        while True:
            if not self._sub:
                self.logger.error("Subscription not initialized, skipping poll")
                await asyncio.sleep(1)
                continue
            msgs = await self._sub.fetch(batch=10, timeout=1)
            for m in msgs:
                await self._safe_handle(m)

    # safe handler
    async def _safe_handle(self, msg) -> None:
        try:
            envelope = json.loads(msg.data.decode())
        except json.JSONDecodeError:
            self.logger.error("Bad JSON on %s", self.subject)
            await msg.ack()
            return

        # Envelope sanity
        for f in ("event_id", "event_type", "data"):
            if f not in envelope:
                self.logger.error("Missing %s; acking", f)
                await msg.ack()
                return
        if envelope["event_type"] != self.subject.split(".", 1)[-1]:
            await msg.ack()
            return

        # Context vars
        set_correlation_id(envelope.get("correlation_id"))
        set_source_service(envelope.get("source_service"))

        # Business logic
        try:
            await self.on_message(envelope["data"])
            await msg.ack()
        except Exception as exc:
            should_ack = await self.on_error(exc, envelope["data"])
            await (msg.ack() if should_ack else msg.nack())

    # default hook
    async def on_error(self, error: Exception, data: dict) -> bool:
        self.logger.error("Error on %s: %s", self.subject, error, exc_info=True)
        return False