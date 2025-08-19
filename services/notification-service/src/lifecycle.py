# services/notification-service/src/lifecycle.py
import asyncio

from prisma import Prisma  # type: ignore[attr-defined]

from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .events.listeners import (
    BillingSubscriptionExpiredListener,
    CatalogSyncCompletedListener,
    CreditBalanceDepletedListener,
    CreditBalanceLowListener,
    MerchantCreatedListener,
)
from .events.publishers import NotificationEventPublisher
from .providers.mailhog_provider import MailhogProvider
from .providers.sendgrid_provider import SendGridProvider
from .repositories.notification_repository import NotificationRepository
from .services.email_service import EmailService
from .services.notification_service import NotificationService
from .services.template_service import TemplateService


class ServiceLifecycle:
    """Manages all service components lifecycle"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # Connections
        self.messaging_client: JetStreamClient | None = None
        self.prisma: Prisma | None = None
        self._db_connected = False

        # Services
        self.notification_service: NotificationService | None = None
        self.template_service: TemplateService | None = None
        self.email_service: EmailService | None = None

        # Event handling
        self.event_publisher: NotificationEventPublisher | None = None
        self._listeners: list = []
        self._tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        """Initialize all components in correct order"""
        try:
            self.logger.info("Starting notification service components...")

            # 1. Messaging
            await self._init_messaging()

            # 2. Database
            await self._init_database()

            # 3. Services
            self._init_services()

            # 4. Event listeners
            await self._init_listeners()

            self.logger.info("Notification service started successfully")

        except Exception:
            self.logger.critical("Service startup failed", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown in reverse order"""
        self.logger.info("Shutting down notification service")

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

        self.logger.info("Notification service shutdown complete")

    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>"])

        # Initialize publisher
        self.event_publisher = NotificationEventPublisher(self.messaging_client, self.logger)

        self.logger.info("Messaging initialized")

    async def _init_database(self) -> None:
        """Initialize Prisma client"""
        if not self.config.database_enabled:
            self.logger.info("Database disabled")
            return

        self.prisma = Prisma()
        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Database connected")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise

    def _init_services(self) -> None:
        """Initialize business services"""
        # Initialize template service
        self.template_service = TemplateService(
            template_path=self.config.template_path,
            cache_ttl=self.config.template_cache_ttl,
            logger=self.logger,
        )

        # Initialize email provider
        if self.config.email_provider == "sendgrid":
            provider = SendGridProvider(
                api_key=self.config.sendgrid_api_key,
                from_email=self.config.sendgrid_from_email,
                from_name=self.config.sendgrid_from_name,
                sandbox_mode=self.config.sendgrid_sandbox_mode,
                logger=self.logger,
            )
        else:
            provider = MailhogProvider(
                smtp_host=self.config.mailhog_smtp_host,
                smtp_port=self.config.mailhog_smtp_port,
                logger=self.logger,
            )

        # Initialize email service
        self.email_service = EmailService(provider=provider, logger=self.logger)

        # Initialize notification service
        if self._db_connected:
            repository = NotificationRepository(self.prisma)
            self.notification_service = NotificationService(
                repository=repository,
                template_service=self.template_service,
                email_service=self.email_service,
                logger=self.logger,
                max_retries=self.config.max_retries,
            )

        self.logger.info("Services initialized")

    async def _init_listeners(self) -> None:
        """Initialize event listeners"""
        if not self.messaging_client or not self.notification_service:
            self.logger.warning("Skipping listeners - dependencies not ready")
            return

        # Create listeners for ALL event types
        listeners = [
            MerchantCreatedListener(
                self.messaging_client,
                self.notification_service,
                self.event_publisher,
                self.logger,
            ),
            CatalogSyncCompletedListener(
                self.messaging_client,
                self.notification_service,
                self.event_publisher,
                self.logger,
            ),
            BillingSubscriptionExpiredListener(
                self.messaging_client,
                self.notification_service,
                self.event_publisher,
                self.logger,
            ),
            CreditBalanceLowListener(
                self.messaging_client,
                self.notification_service,
                self.event_publisher,
                self.logger,
            ),
            CreditBalanceDepletedListener(
                self.messaging_client,
                self.notification_service,
                self.event_publisher,
                self.logger,
            ),
        ]

        # Start all listeners
        for listener in listeners:
            await listener.start()
            self._listeners.append(listener)

        self.logger.info(f"Started {len(listeners)} event listeners")
