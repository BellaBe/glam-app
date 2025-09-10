# shared/shared/messaging/jetstream_client.py
"""Pure JetStream client with connection and stream management."""

import os

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.api import RetentionPolicy, StorageType, StreamConfig
from nats.js.errors import NotFoundError

from shared.utils.logger import ServiceLogger


class JetStreamClient:
    """JetStream client with connection pooling and stream management."""

    def __init__(self, logger: ServiceLogger) -> None:
        self._client: Client | None = None
        self._js: JetStreamContext | None = None
        self.logger = logger

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_t, exc, tb):
        await self.close()

    @property
    def client(self) -> Client:
        if not self._client:
            raise RuntimeError("NATS client not connected")
        return self._client

    @property
    def js(self) -> JetStreamContext:
        if not self._js:
            raise RuntimeError("JetStream not initialized")
        return self._js

    async def connect(self, servers: list[str]) -> None:
        """Connect to NATS and initialize JetStream."""
        opts = {
            "servers": servers,
            "max_reconnect_attempts": -1,
            "reconnect_time_wait": 2,
        }

        if user := os.getenv("NATS_USER"):
            opts.update(user=user, password=os.getenv("NATS_PASSWORD", ""))

        self._client = await nats.connect(**opts)
        self._js = self._client.jetstream()

        # Verify JetStream is accessible
        try:
            info = await self._js.account_info()
            self.logger.info(
                f"Connected to NATS {servers}, JetStream ready (streams: {info.streams}, consumers: {info.consumers})"
            )
        except Exception as e:
            self.logger.error(f"JetStream not accessible: {e}")
            raise RuntimeError(f"JetStream initialization failed: {e}")

    async def close(self) -> None:
        """Close NATS connection."""
        if self._client and not self._client.is_closed:
            await self._client.close()
            self.logger.info("NATS connection closed")

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return bool(self._client and self._client.is_connected)

    async def ensure_stream(
        self,
        name: str,
        subjects: list[str],
        max_age: int = 24 * 60 * 60,
        max_msgs: int = 1_000_000,
    ) -> None:
        """Ensure stream exists with given configuration."""
        if not self._js:
            raise RuntimeError("JetStream not initialized")

        cfg = StreamConfig(
            name=name,
            subjects=subjects,
            retention=RetentionPolicy.LIMITS,
            max_age=max_age,
            max_msgs=max_msgs,
            storage=StorageType.FILE,
        )

        try:
            info = await self._js.stream_info(name)
            self.logger.info(f"Stream '{name}' exists with subjects: {info.config.subjects}")
        except NotFoundError:
            await self._js.add_stream(cfg)
            self.logger.info(f"Created stream '{name}' with subjects: {subjects}")
