# shared/messaging/js_listener.py
"""A thin, “safe” JetStream listener with JSON decode guard and error handling."""

import asyncio
import contextlib
import json
from abc import ABC, abstractmethod
from typing import Any

from nats.errors import TimeoutError as NATSTimeoutError
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from nats.js.errors import NotFoundError

from shared.utils.logger import ServiceLogger

from .jetstream_client import JetStreamClient

# from .event_context import set_correlation_id, set_source_service


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
    _task: asyncio.Task | None = None
    _running: bool = False
    idle_sleep_sec: float = 0.05  # avoid spin when idle
    poll_window_sec: float = 2.0  # server-side fetch window

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

    async def start(self) -> None:
        await self._ensure_stream()
        await self._ensure_consumer()
        await self._create_subscription()
        self.logger.info("Listening on %s", self.subject)
        self._running = True
        self._task = asyncio.create_task(self._poll_loop(), name=f"{self.service_name}:{self.subject}")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._sub:
            await self._sub.unsubscribe()

    @abstractmethod
    async def on_message(self, data: dict[str, Any]) -> None: ...

    # stream
    async def _ensure_stream(self) -> None:
        """Stream must exist and cover ``evt.*`` **and** ``cmd.*``."""
        from nats.js.api import RetentionPolicy, StorageType, StreamConfig  # local to avoid circulars

        try:
            await self._js.stream_info(self.stream_name)
        except NotFoundError:
            cfg = StreamConfig(
                name=self.stream_name,
                subjects=["evt.>", "cmd.>"],
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
                max_ack_pending=self.batch_size * 5,  # tame inflight
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

    async def _poll_loop(self) -> None:
        try:
            while self._running:
                if not self._sub:
                    self.logger.error("Subscription not initialized, skipping poll")
                    await asyncio.sleep(1)
                    continue
                try:
                    msgs = await self._sub.fetch(
                        batch=self.batch_size,
                        timeout=self.poll_window_sec,
                    )
                except (TimeoutError, NATSTimeoutError):
                    # Normal: no messages in window
                    await asyncio.sleep(self.idle_sleep_sec)
                    continue

                if not msgs:
                    await asyncio.sleep(self.idle_sleep_sec)
                    continue

                for m in msgs:
                    await self._safe_handle(m)

        except asyncio.CancelledError:
            self.logger.info("Poll loop cancelled for %s", self.subject)
        except Exception:
            self.logger.critical("Poll loop crashed for %s", self.subject)
        # no finally cleanup here; stop() handles unsubscribe

    # safe handler
    async def _safe_handle(self, msg) -> None:
        try:
            envelope = json.loads(msg.data.decode())
        except json.JSONDecodeError:
            self.logger.error("Bad JSON on %s; acking (dropping)", self.subject)
            await msg.ack()
            return

        for f in ("event_id", "event_type", "data"):
            if f not in envelope:
                self.logger.error("Missing %s; acking (dropping)", f)
                await msg.ack()
                return

        if envelope.get("event_type") and envelope["event_type"] != self.subject:
            self.logger.warning(
                "Event-type mismatch; acking (subject=%s, event_type=%s)", self.subject, envelope["event_type"]
            )
            await msg.ack()
            return

        md = getattr(msg, "metadata", None)
        if md and getattr(md, "num_delivered", None) is not None and md.num_delivered >= self.max_deliver:
            self.logger.error("Final delivery hit; dropping msg on subject %s", self.subject)

        try:
            await self.on_message(envelope["data"])
            await msg.ack()
        except Exception as exc:
            should_ack = await self.on_error(exc, envelope["data"])
            try:
                if should_ack:
                    await msg.ack()
                else:
                    await msg.nak()
            except Exception:
                self.logger.critical("Failed to ack/nak message")

    # default hook
    async def on_error(self, error: Exception, data: dict) -> bool:
        self.logger.error("Error on %s: %s", self.subject, error, exc_info=True)
        return False
