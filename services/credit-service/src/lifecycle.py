# services/credit-service/src/lifecycle.py
import asyncio

from prisma import Prisma  # type: ignore[attr-defined]

from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .events.listeners import (
    CreditsPurchasedListener,
    MatchCompletedListener,
    MerchantCreatedListener,
    TrialStartedListener,
)
from .events.publishers import CreditEventPublisher
from .repositories.credit_repository import CreditRepository
from .services.credit_service import CreditService


class ServiceLifecycle:
    """Manages all service components lifecycle"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # Connections
        self.messaging_client: JetStreamClient | None = None
        self.prisma: Prisma | None = None
        self._db_connected = False

        # Components
        self.event_publisher: CreditEventPublisher | None = None
        self.credit_repo: CreditRepository | None = None
        self.credit_service: CreditService | None = None

        # Listeners
        self._listeners: list = []
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        """Initialize all components in correct order"""
        try:
            self.logger.info("Starting credit service components...")

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

            self.logger.info("Credit service started successfully")

        except Exception:
            self.logger.critical("Service startup failed", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown in reverse order"""
        self.logger.info("Shutting down credit service")

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
                self.logger.error("Listener stop failed", exc_info=True)

        # Close messaging
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.error("Messaging close failed", exc_info=True)

        # Disconnect database
        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.error("Prisma disconnect failed", exc_info=True)

        self.logger.info("Credit service shutdown complete")

    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>"])

        # Initialize publisher
        self.event_publisher = CreditEventPublisher(jetstream_client=self.messaging_client, logger=self.logger)

        self.logger.info("Messaging client and publisher initialized")

    async def _init_database(self) -> None:
        """Initialize Prisma client"""
        if not self.config.database_enabled:
            self.logger.info("Database disabled")
            return

        self.prisma = Prisma()
        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Prisma connected")
        except Exception as e:
            self.logger.error(f"Prisma connect failed: {e}", exc_info=True)
            raise

    def _init_repositories(self) -> None:
        """Initialize repositories"""
        if not self._db_connected:
            self.logger.warning("Database not connected")
            return

        self.credit_repo = CreditRepository(self.prisma)
        self.logger.info("Credit repository initialized")

    def _init_services(self) -> None:
        """Initialize business services"""
        if not self.credit_repo:
            raise RuntimeError("Credit repository not initialized")

        self.credit_service = CreditService(repository=self.credit_repo, config=self.config, logger=self.logger)
        self.logger.info("Credit service initialized")

    async def _init_listeners(self) -> None:
        """Initialize and start event listeners"""
        if not self.messaging_client or not self.credit_service:
            raise RuntimeError("Dependencies not ready")

        # Create listeners
        listeners = [
            MerchantCreatedListener(
                js_client=self.messaging_client,
                service=self.credit_service,
                publisher=self.event_publisher,
                logger=self.logger,
            ),
            TrialStartedListener(
                js_client=self.messaging_client,
                service=self.credit_service,
                publisher=self.event_publisher,
                logger=self.logger,
            ),
            CreditsPurchasedListener(
                js_client=self.messaging_client,
                service=self.credit_service,
                publisher=self.event_publisher,
                logger=self.logger,
            ),
            MatchCompletedListener(
                js_client=self.messaging_client,
                service=self.credit_service,
                publisher=self.event_publisher,
                logger=self.logger,
            ),
        ]

        # Start all listeners
        for listener in listeners:
            await listener.start()
            self._listeners.append(listener)

        self.logger.info(f"Started {len(listeners)} event listeners")
