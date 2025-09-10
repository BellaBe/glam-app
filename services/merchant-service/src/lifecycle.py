# services/merchant-service/src/lifecycle.py
import asyncio
import time

from prisma import Prisma  # type: ignore[attr-defined]

from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .events.listeners import AppUninstalledListener
from .events.publishers import MerchantEventPublisher
from .repositories import MerchantRepository
from .services.merchant_service import MerchantService


class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # External connections
        self.messaging_client: JetStreamClient | None = None
        self.prisma: Prisma | None = None
        self._db_connected: bool = False

        # Publisher / listeners
        self.event_publisher: MerchantEventPublisher | None = None
        self._listeners: list = []

        # Repositories / mappers / services
        self.merchant_repo: MerchantRepository | None = None
        self.merchant_service: MerchantService | None = None

        self.event_publisher: MerchantEventPublisher | None = None

        # Tasks
        self._listeners: list = []
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        try:
            self.logger.info("Starting merchant service components...")
            start_time = time.time()
            # 1. Messaging
            await self._init_messaging()

            # 2. Database
            await self._init_database()

            # 3. Repositories
            self._init_repositories()

            # 4. Services
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

        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.exception("Prisma disconnect failed", exc_info=True)

        self.logger.info("%s shutdown complete", self.config.service_name)

    async def _init_messaging(self) -> None:
        """Initialize JetStream client and publisher"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        # await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>", "dlq.>"])

        # Initialize publisher now (you require it in _init_listeners)
        self.event_publisher = MerchantEventPublisher(self.messaging_client, self.logger)

        self.logger.info("Messaging client and publisher initialized")

    async def _init_database(self) -> None:
        """Initialize Prisma client if database is enabled."""
        if not self.config.database_enabled:
            self.logger.info("Database disabled; skipping Prisma initialization")
            return

        # Prisma reads DATABASE_URL from the environment; no args needed
        self.prisma = Prisma()
        if not self.prisma:
            raise RuntimeError("Prisma client not initialized")

        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Database connected")
        except Exception as e:
            self.logger.exception("Database connect failed: %s", e, exc_info=True)
            raise

    def _init_repositories(self) -> None:
        if self.config.database_enabled:
            if not (self.prisma and self._db_connected):
                raise RuntimeError("Prisma client not initialized/connected")
            self.merchant_repo = MerchantRepository(self.prisma)
            self.logger.info("Merchant repository initialized")
        else:
            self.merchant_repo = None  # service must handle db-disabled mode

    def _init_services(self) -> None:
        if not self.merchant_repo or not self.event_publisher:
            raise RuntimeError("Merchant repository not initialized")

        self.merchant_service = MerchantService(
            repository=self.merchant_repo, publisher=self.event_publisher, logger=self.logger
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
