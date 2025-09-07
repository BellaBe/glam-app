import asyncio

from prisma import Prisma  # type: ignore[attr-defined]

from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .events.listeners import MerchantCreatedListener, PurchaseWebhookListener
from .events.publishers import BillingEventPublisher
from .repositories.billing_repository import BillingRepository
from .repositories.purchase_repository import PurchaseRepository
from .services.billing_service import BillingService
from .services.purchase_service import PurchaseService
from .utils.credit_packs import CreditPackManager
from .utils.shopify_client import ShopifyClient


class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # External connections
        self.messaging_client: JetStreamClient | None = None
        self.prisma: Prisma | None = None
        # self.redis: redis.Redis | None = None
        self._db_connected: bool = False

        # Publishers / listeners
        self.event_publisher: BillingEventPublisher | None = None
        self._listeners: list = []

        # Repositories
        self.billing_repo: BillingRepository | None = None
        self.purchase_repo: PurchaseRepository | None = None

        # Services
        self.billing_service: BillingService | None = None
        self.purchase_service: PurchaseService | None = None

        # Utils
        self.pack_manager: CreditPackManager | None = None
        self.shopify_client: ShopifyClient | None = None

        # Tasks
        self._tasks: list[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

    async def startup(self) -> None:
        """Initialize all components"""
        try:
            self.logger.info("Starting service components...")

            await self._init_messaging()
            await self._init_database()
            # await self._init_redis()
            self._init_utils()
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

        # Cancel tasks
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Stop listeners
        for lst in self._listeners:
            try:
                await lst.stop()
            except Exception:
                self.logger.critical("Listener stop failed", exc_info=True)

        # # Close connections
        # if self.redis:
        #     try:
        #         await self.redis.close()
        #         if hasattr(self.redis, "wait_closed"):
        #             await self.redis.wait_closed()
        #     except Exception:
        #         self.logger.critical("Redis close failed", exc_info=True)

        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.critical("Messaging client close failed", exc_info=True)

        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.critical("Prisma disconnect failed", exc_info=True)

        self.logger.info("%s shutdown complete", self.config.service_name)

    async def _init_messaging(self) -> None:
        """Initialize messaging client"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>"])

        # Initialize publisher
        self.event_publisher = BillingEventPublisher(
            jetstream_client=self.messaging_client,
            logger=self.logger,
        )

        self.logger.info("Messaging client and publisher initialized")

    async def _init_database(self) -> None:
        """Initialize Prisma client"""
        if not self.config.database_enabled:
            self.logger.info("Database disabled; skipping Prisma initialization")
            return

        self.prisma = Prisma()
        if not self.prisma:
            raise RuntimeError("Prisma client not initialized")

        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Prisma connected")
        except Exception as e:
            self.logger.exception("Prisma connect failed: %s", e, exc_info=True)
            raise

    # async def _init_redis(self) -> None:
    #     """Initialize Redis client"""
    #     self.redis = redis.from_url(self.config.redis_url)
    #     await self.redis.ping()
    #     self.logger.info("Redis connected")

    def _init_utils(self) -> None:
        """Initialize utility classes"""
        self.pack_manager = CreditPackManager(self.config)
        self.shopify_client = ShopifyClient(self.config, self.logger)
        self.logger.info("Utilities initialized")

    def _init_repositories(self) -> None:
        """Initialize repositories"""
        if self.config.database_enabled:
            if not (self.prisma and self._db_connected):
                raise RuntimeError("Prisma client not initialized/connected")

            self.billing_repo = BillingRepository(self.prisma, self.logger)
            self.purchase_repo = PurchaseRepository(self.prisma, self.logger)
            self.logger.info("Repositories initialized")
        else:
            self.billing_repo = None
            self.purchase_repo = None

    def _init_local_services(self) -> None:
        """Initialize services"""
        if not self.billing_repo or not self.purchase_repo:
            raise RuntimeError("Repositories not initialized")

        if not self.event_publisher:
            raise RuntimeError("Event publisher not initialized")

        # # Add checks for required dependencies
        # if not self.redis:
        #     raise RuntimeError("Redis client not initialized")

        if not self.pack_manager:
            raise RuntimeError("Credit pack manager not initialized")

        if not self.shopify_client:
            raise RuntimeError("Shopify client not initialized")

        self.billing_service = BillingService(
            config=self.config,
            billing_repo=self.billing_repo,
            purchase_repo=self.purchase_repo,
            publisher=self.event_publisher,
            logger=self.logger,
        )

        self.purchase_service = PurchaseService(
            config=self.config,
            billing_repo=self.billing_repo,
            purchase_repo=self.purchase_repo,
            pack_manager=self.pack_manager,
            shopify_client=self.shopify_client,
            publisher=self.event_publisher,
            logger=self.logger,
        )

        self.logger.info("Services initialized")

    async def _init_listeners(self) -> None:
        """Initialize event listeners"""
        if not self.messaging_client or not self.billing_service or not self.purchase_service:
            raise RuntimeError("Required components not ready for listeners")

        # Merchant created listener
        merchant_listener = MerchantCreatedListener(
            js_client=self.messaging_client, billing_service=self.billing_service, logger=self.logger
        )
        await merchant_listener.start()
        self._listeners.append(merchant_listener)

        # Purchase webhook listener
        webhook_listener = PurchaseWebhookListener(
            js_client=self.messaging_client, purchase_service=self.purchase_service, logger=self.logger
        )
        await webhook_listener.start()
        self._listeners.append(webhook_listener)

        self.logger.info("Event listeners started")

    def add_task(self, coro) -> asyncio.Task:
        """Add a background task"""
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal"""
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        """Signal shutdown"""
        self._shutdown_event.set()
