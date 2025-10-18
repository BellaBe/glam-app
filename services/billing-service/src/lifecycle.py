# services/billing-service/src/lifecycle.py
import asyncio
import time

from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .db.session import make_engine, make_session_factory
from .events.listeners import (
    MerchantCreatedListener,
    PurchaseUpdatedListener,
    PurchaseRefundedListener,
)
from .events.publishers import BillingEventPublisher
from .services.billing_service import BillingService
from .services.shopify_adapter import ShopifyAdapter


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
        self.event_publisher: BillingEventPublisher | None = None
        self._listeners: list = []

        # Adapters
        self.shopify_adapter: ShopifyAdapter | None = None

        # Services
        self.billing_service: BillingService | None = None

        # Tasks
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        try:
            self.logger.info("Starting billing service components...")
            start_time = time.time()
            
            # 1. Messaging
            await self._init_messaging()

            # 2. Database
            await self._init_database()

            # 3. Platform adapters
            self._init_adapters()

            # 4. Services
            self._init_services()

            # 5. Event listeners
            await self._init_listeners()

            # 6. Background tasks
            self._start_background_tasks()

            self.logger.info(
                f"{self.config.service_name} started successfully "
                f"in {time.time() - start_time:.2f}s"
            )

        except Exception:
            self.logger.critical("Service failed to start", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info("Shutting down %s", self.config.service_name)

        # Cancel background tasks
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
                self.logger.exception(
                    "Messaging client close failed",
                    exc_info=True
                )

        # Dispose database
        if self.engine:
            try:
                await self.engine.dispose()
            except Exception:
                self.logger.exception(
                    "Engine dispose failed",
                    exc_info=True
                )

        self.logger.info("%s shutdown complete", self.config.service_name)

    async def _init_messaging(self) -> None:
        """Initialize JetStream client and publisher"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream(
            "GLAM_EVENTS",
            ["evt.*", "cmd.*"]
        )

        self.event_publisher = BillingEventPublisher(
            self.messaging_client,
            self.logger
        )
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
            self.logger.exception(
                "Database connect failed: %s",
                e,
                exc_info=True
            )
            raise

    def _init_adapters(self) -> None:
        """Initialize platform adapters"""
        self.shopify_adapter = ShopifyAdapter(
            config=self.config,
            logger=self.logger,
        )
        self.logger.info("Platform adapters initialized")

    def _init_services(self) -> None:
        if not self.session_factory or not self.event_publisher:
            raise RuntimeError("Session factory or publisher not ready")

        self.billing_service = BillingService(
            session_factory=self.session_factory,
            publisher=self.event_publisher,
            platform_adapter=self.shopify_adapter,
            logger=self.logger,
        )
        self.logger.info("Billing service initialized")

    async def _init_listeners(self) -> None:
        if not self.messaging_client or not self.billing_service:
            raise RuntimeError("Messaging or service layer not ready")

        listeners = [
            MerchantCreatedListener(
                self.messaging_client,
                self.billing_service,
                self.logger
            ),
            PurchaseUpdatedListener(
                self.messaging_client,
                self.billing_service,
                self.logger
            ),
            PurchaseRefundedListener(
                self.messaging_client,
                self.billing_service,
                self.logger
            ),
        ]
        
        for listener in listeners:
            await listener.start()
            self._listeners.append(listener)
            self.logger.info("Listener started: %s", listener.subject)

    def _start_background_tasks(self) -> None:
        """Start background cleanup tasks"""
        cleanup_task = asyncio.create_task(self._cleanup_expired_payments())
        self._tasks.append(cleanup_task)
        self.logger.info("Background tasks started")

    async def _cleanup_expired_payments(self) -> None:
        """Periodic cleanup of expired payments"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                if self.billing_service:
                    await self.billing_service.cleanup_expired_payments()
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception(
                    "Cleanup task failed",
                    exc_info=True
                )
