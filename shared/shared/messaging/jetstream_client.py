# shared/shared/messaging/jetstream_client.py
"""Pure JetStream client - only connection + stream management."""

import os

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.api import RetentionPolicy, StorageType, StreamConfig
from nats.js.errors import NotFoundError

from shared.utils.logger import ServiceLogger


class JetStreamClient:
    """Pure JetStream client - only connection + stream management."""

    def __init__(self, logger: ServiceLogger) -> None:  # ✔ typed
        self._client: Client | None = None
        self._js: JetStreamContext | None = None
        self.logger = logger

    # context-manager helpers --------------------------------------------------
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_t, exc, tb):
        await self.close()

    # public accessors ---------------------------------------------------------
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

    # connection ---------------------------------------------------------------
    async def connect(self, servers: list[str]) -> None:
        opts = {
            "servers": servers,
            "max_reconnect_attempts": -1,
            "reconnect_time_wait": 2,
        }
        if user := os.getenv("NATS_USER"):
            opts.update(user=user, password=os.getenv("NATS_PASSWORD", ""))

        self._client = await nats.connect(**opts)
        self._js = self._client.jetstream()
        if self.logger:
            self.logger.info("Connected to NATS %s", servers)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.close()
            if self.logger:
                self.logger.info("NATS connection closed")

    def is_connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    # stream helpers -----------------------------------------------------------
    async def ensure_stream(
        self,
        name: str,
        subjects: list[str],
        **kw,
    ) -> None:
        if not self._js:
            raise RuntimeError("JetStream not initialized")

        cfg = StreamConfig(
            name=name,
            subjects=subjects,
            retention=RetentionPolicy.LIMITS,
            max_age=24 * 60 * 60,
            max_msgs=1_000_000,
            storage=StorageType.FILE,
        )

        try:
            await self._js.stream_info(name)
            if self.logger:
                self.logger.debug("Using existing stream: %s", name)
        except NotFoundError:
            await self._js.add_stream(cfg)
            if self.logger:
                self.logger.info("Created new stream: %s", name)

    async def delete_stream(self, name: str) -> None:
        if not self._js:
            raise RuntimeError("JetStream not initialized")
        await self._js.delete_stream(name)
        if self.logger:
            self.logger.info("Deleted stream: %s", name)

    async def get_stream_info(self, name: str) -> dict:
        if not self._js:
            raise RuntimeError("JetStream not initialized")
        info = await self._js.stream_info(name)
        return {
            "name": info.config.name,
            "subjects": info.config.subjects,
            "messages": info.state.messages,
            "bytes": info.state.bytes,
        }
