# services/merchant-service/src/lifecycle.py
from typing import Optional, List, Dict, Any
import asyncio
from prisma import Prisma
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from .config import ServiceConfig
from .repositories import MerchantRepository
from .services.merchant_service import MerchantService
from .events.publishers import MerchantEventPublisher

class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # External connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.prisma: Optional[Prisma] = None
        self._db_connected: bool = False

        # Publisher / listeners
        self.event_publisher: Optional[MerchantEventPublisher] = None
        self._listeners: list = []

        # Repositories / mappers / services
        self.merchant_repo: Optional[MerchantRepository] = None
        self.merchant_service: Optional[MerchantService] = None

        # Tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

    async def startup(self) -> None:
        try:
            self.logger.info("Starting service components...")
            await self._init_messaging()
            await self._init_database()
            self._init_repositories()
            self._init_local_services()
            await self._init_listeners()
            self.logger.info("%s started successfully", self.config.service_name)
        except Exception:
            self.logger.critical("Service failed to start", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info("Shutting down %s", self.config.service_name)

        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        for lst in self._listeners:
            try:
                await lst.stop()
            except Exception:
                self.logger.critical("Listener stop failed")

        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.critical("Messaging client close failed")

        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.critical("Prisma disconnect failed")

        self.logger.info("%s shutdown complete", self.config.service_name)

    async def _init_messaging(self) -> None:
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>"])

        # Initialize publisher now (you require it in _init_listeners)
        self.event_publisher = MerchantEventPublisher(
            jetstream_client=self.messaging_client,
            logger=self.logger
        )
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
            self.logger.info("Prisma connected")
        except Exception as e:
            # Be explicit; this usually means DATABASE_URL is missing/invalid or client not generated
            self.logger.error("Prisma connect failed: %s", e, exc_info=True)
            raise

    # ---------------------------------------------------------------- repos
    def _init_repositories(self) -> None:
        if self.config.database_enabled:
            if not (self.prisma and self._db_connected):
                raise RuntimeError("Prisma client not initialized/connected")
            self.merchant_repo = MerchantRepository(self.prisma)
            self.logger.info("Merchant repository initialized")
        else:
            self.merchant_repo = None  # service must handle db-disabled mode

    # ---------------------------------------------------------- local services
    def _init_local_services(self) -> None:
        
        if not self.merchant_repo or not self.event_publisher:
            raise RuntimeError("Merchant repository not initialized")
        
        self.merchant_service = MerchantService(
            repository=self.merchant_repo,
            publisher=self.event_publisher,
            logger=self.logger
            
        )

    # -------------------------------------------------------------- listeners
    async def _init_listeners(self) -> None:
        if not self.messaging_client or not self.merchant_service or not self.event_publisher:
            raise RuntimeError("Messaging or service layer not ready")

        # Initialize and start subscribers here when you add them
        # await some_listener.start()
        # self._listeners.append(some_listener)

    # ================================================= convenience helpers
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        self._shutdown_event.set()
