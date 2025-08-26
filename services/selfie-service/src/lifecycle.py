# services/selfie-service/src/lifecycle.py
import asyncio

from prisma import Prisma

from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .events.publishers import SelfieEventPublisher
from .repositories.analysis_repository import AnalysisRepository
from .services.image_processor import ImageProcessor
from .services.selfie_service import SelfieService


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
        self.event_publisher: SelfieEventPublisher | None = None
        self.analysis_repo: AnalysisRepository | None = None
        self.image_processor: ImageProcessor | None = None
        self.selfie_service: SelfieService | None = None

        # Listeners
        self._listeners: list = []
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        """Initialize all components in correct order"""
        try:
            self.logger.info("Starting selfie service components...")

            # 1. Messaging (for events)
            await self._init_messaging()

            # 2. Database
            await self._init_database()

            # 3. Repositories (depends on Prisma)
            self._init_repositories()

            # 4. Core services
            self._init_services()

            # 5. Event listeners (optional for MVP)
            # await self._init_listeners()

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

        self.logger.info(f"{self.config.service_name} shutdown complete")

    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream for events"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])

        # Initialize publisher
        self.event_publisher = SelfieEventPublisher(jetstream_client=self.messaging_client, logger=self.logger)
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
            self.logger.error(f"Prisma connect failed: {e}", exc_info=True)
            raise

    def _init_repositories(self) -> None:
        """Initialize repositories with Prisma client"""
        if not self._db_connected:
            self.logger.warning("Database not connected, skipping repositories")
            return

        self.analysis_repo = AnalysisRepository(self.prisma)
        self.logger.info("Analysis repository initialized")

    def _init_services(self) -> None:
        """Initialize business services"""
        # Initialize image processor
        self.image_processor = ImageProcessor(config=self.config, logger=self.logger)

        # Initialize selfie service
        if not self.analysis_repo:
            raise RuntimeError("Analysis repository not initialized")

        self.selfie_service = SelfieService(
            repository=self.analysis_repo, image_processor=self.image_processor, config=self.config, logger=self.logger
        )

        self.logger.info("Selfie service initialized")

    async def _init_listeners(self) -> None:
        """Initialize event listeners (optional)"""
        if not self.messaging_client or not self.selfie_service:
            raise RuntimeError("Messaging or service not ready")

        # Example: Listen for completed analyses from other services
        # listener = AnalysisCompletedListener(
        #     js_client=self.messaging_client,
        #     service=self.selfie_service,
        #     logger=self.logger
        # )
        # await listener.start()
        # self._listeners.append(listener)

        self.logger.info("Event listeners started")
