# services/merchant-service/src/lifecycle.py
import asyncio
import time

from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from src.db.session import make_engine, make_session_factory
from src.events.publishers import MerchantEventPublisher
from src.services.merchant_service import MerchantService

from .config import ServiceConfig
from .events.listeners import AppUninstalledListener
from .events.publishers import MerchantEventPublisher
from .services.merchant_service import MerchantService


class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # External connections
        self.messaging_client: JetStreamClient | None = None
        self.engine = None
        self.session_factory = None

        # Publisher / listeners
        self.event_publisher: MerchantEventPublisher | None = None
        self._listeners: list = []

        # Services
        self.merchant_service: MerchantService | None = None

        # Tasks
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        try:
            self.logger.info("Starting merchant service components...")
            start_time = time.time()
            # 1. Messaging
            await self._init_messaging()

            # 2. Database
            await self._init_database()

            # 3. Services
            self._init_services()

            # 5. Event listeners
            await self._init_listeners()

            self.logger.info(f"Merchant service started successfully in {time.time() - start_time:.2f}s")

        except Exception:
            self.logger.critical("Service failed to start", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info("Shutting down %s", self.config.service_name)

        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        for listener in self._listeners:
            try:
                await listener.stop()
            except Exception:
                self.logger.exception("Listener stop failed", exc_info=True)

        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.exception("Messaging client close failed", exc_info=True)

        if self.engine:
            try:
                await self.engine.dispose()
            except Exception:
                self.logger.exception("Engine dispose failed", exc_info=True)

        self.logger.info("%s shutdown complete", self.config.service_name)

    async def _init_messaging(self) -> None:
        """Initialize JetStream client and publisher"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>"])

        # Initialize publisher
        self.event_publisher = MerchantEventPublisher(self.messaging_client, self.logger)
        self.logger.info("Messaging client and publisher initialized")

    async def _init_database(self) -> None:
        """Initialize database manager if database is enabled."""
        if not self.config.database_enabled:
            self.logger.info("Database disabled; skipping initialization")
            return

        try:
            self.engine = make_engine(self.config.database_url)
            self.session_factory = make_session_factory(self.engine)
            self.logger.info("Database initialized")
        except Exception as e:
            self.logger.exception("Database connect failed: %s", e, exc_info=True)
            raise

    def _init_services(self) -> None:
        if not self.session_factory or not self.event_publisher:
            raise RuntimeError("Session factory or publisher not ready")

        self.merchant_service = MerchantService(
            session_factory=self.session_factory, publisher=self.event_publisher, logger=self.logger
        )
        self.logger.info("Merchant service initialized")

    async def _init_listeners(self) -> None:
        if not self.messaging_client or not self.merchant_service or not self.event_publisher:
            raise RuntimeError("Messaging or service layer not ready")

        listeners = [
            AppUninstalledListener(self.messaging_client, self.merchant_service, self.logger),
        ]
        for listener in listeners:
            await listener.start()
            self._listeners.append(listener)
            self.logger.info("Listener started: %s", listener.subject)
