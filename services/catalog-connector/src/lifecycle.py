# services/platform-connector/src/lifecycle.py
import asyncio

from shared.messaging import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .events.listeners import CatalogSyncRequestedListener
from .events.publishers import PlatformEventPublisher
from .services.connector_service import ConnectorService


class ServiceLifecycle:
    """Manages all service components lifecycle"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # Connections
        self.messaging_client: JetStreamClient | None = None

        # Components
        self.event_publisher: PlatformEventPublisher | None = None
        self.connector_service: ConnectorService | None = None

        # Listeners
        self._listeners: list = []
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        """Initialize all components"""
        try:
            self.logger.info("Starting platform connector components...")

            # 1. Messaging (for events)
            await self._init_messaging()

            # 2. Services
            self._init_services()

            # 3. Event listeners
            await self._init_listeners()

            self.logger.info("Platform connector started successfully")

        except Exception:
            self.logger.critical("Service startup failed", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.info("Shutting down platform connector")

        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Stop listeners
        for listener in self._listeners:
            try:
                await listener.stop()
            except Exception:
                self.logger.exception("Listener stop failed", exc_info=True)

        # Close messaging
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.exception("Messaging close failed", exc_info=True)

        self.logger.info("Platform connector shutdown complete")

    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>"])

        # Initialize publisher
        self.event_publisher = PlatformEventPublisher(jetstream_client=self.messaging_client, logger=self.logger)

        self.logger.info("Messaging initialized")

    def _init_services(self) -> None:
        """Initialize business services"""
        self.connector_service = ConnectorService(
            event_publisher=self.event_publisher, logger=self.logger, config=vars(self.config)
        )

        self.logger.info("Connector service initialized")

    async def _init_listeners(self) -> None:
        """Initialize event listeners"""
        if not self.messaging_client or not self.connector_service:
            raise RuntimeError("Messaging or service not ready")

        # Catalog sync requested listener
        sync_listener = CatalogSyncRequestedListener(
            js_client=self.messaging_client, connector_service=self.connector_service, logger=self.logger
        )
        await sync_listener.start()
        self._listeners.append(sync_listener)

        self.logger.info("Event listeners started")
