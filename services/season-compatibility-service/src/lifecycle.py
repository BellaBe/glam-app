# services/season-compatibility/src/lifecycle.py
import asyncio

from prisma import Prisma

from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .events.listeners import AIAnalysisCompletedListener
from .events.publishers import SeasonEventPublisher
from .repositories.compatibility_repository import CompatibilityRepository
from .services.compatibility_service import CompatibilityService


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
        self.event_publisher: SeasonEventPublisher | None = None
        self.compatibility_repo: CompatibilityRepository | None = None
        self.compatibility_service: CompatibilityService | None = None

        # Listeners
        self._listeners: list = []
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        """Initialize all components in correct order"""
        try:
            self.logger.info("Starting service components...")

            # 1. Messaging (for events)
            await self._init_messaging()

            # 2. Database
            await self._init_database()

            # 3. Repositories (depends on Prisma)
            self._init_repositories()

            # 4. Services (depends on repositories)
            self._init_services()

            # 5. Event listeners (depends on services)
            await self._init_listeners()

            self.logger.info(f"{self.config.service_name} started successfully")

        except Exception:
            self.logger.critical("Service startup failed", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown in reverse order"""
        self.logger.info(f"Shutting down {self.config.service_name}")

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

        # Disconnect database
        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.exception("Prisma disconnect failed", exc_info=True)

        self.logger.info(f"{self.config.service_name} shutdown complete")

    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream for events"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>"])

        # Initialize publisher
        self.event_publisher = SeasonEventPublisher(jetstream_client=self.messaging_client, logger=self.logger)
        self.logger.info("Messaging client and publisher initialized")

    async def _init_database(self) -> None:
        """Initialize Prisma client"""
        if not self.config.database_enabled:
            self.logger.info("Database disabled; skipping Prisma initialization")
            return

        self.prisma = Prisma()
        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Prisma connected")
        except Exception as e:
            self.logger.exception(f"Prisma connect failed: {e}", exc_info=True)
            raise

    def _init_repositories(self) -> None:
        """Initialize repositories with Prisma client"""
        if not self._db_connected:
            self.logger.warning("Database not connected, skipping repositories")
            return

        self.compatibility_repo = CompatibilityRepository(self.prisma)
        self.logger.info("Compatibility repository initialized")

    def _init_services(self) -> None:
        """Initialize business services"""
        if not self.compatibility_repo:
            raise RuntimeError("Compatibility repository not initialized")

        self.compatibility_service = CompatibilityService(repository=self.compatibility_repo, logger=self.logger)
        self.logger.info("Compatibility service initialized")

    async def _init_listeners(self) -> None:
        """Initialize event listeners"""
        if not self.messaging_client or not self.compatibility_service:
            raise RuntimeError("Messaging or service not ready")

        # Create AI analysis listener
        listener = AIAnalysisCompletedListener(
            js_client=self.messaging_client,
            publisher=self.event_publisher,
            service=self.compatibility_service,
            logger=self.logger,
        )

        # Start listener
        await listener.start()
        self._listeners.append(listener)

        self.logger.info("Event listeners started")
