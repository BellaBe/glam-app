from __future__ import annotations

import asyncio
from typing import List, Optional

from shared.utils.logger import ServiceLogger
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_client import JetStreamClient

from .config import ServiceConfig
from .services.email_service import EmailService
from .services.notification_service import NotificationService
from .services.template_service import TemplateService
from .repositories.notification_repository import NotificationRepository
from .models.notification import Notification

# messaging
from .events.publishers   import EmailSendPublisher
from .events.listeners import SendEmailListener, SendBulkEmailListener
from .mappers.notification_mapper import NotificationMapper


class ServiceLifecycle:
    """Manages the lifecycle of the notification service, including initialization and shutdown."""

    # ------------------------------------------------------------------ ctor
    def __init__(self, config: ServiceConfig, logger: ServiceLogger) -> None:
        self.config  = config
        self.logger  = logger

        # External connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.db_manager:      Optional[DatabaseSessionManager] = None

        # Publisher
        self.email_send_publisher: Optional[EmailSendPublisher] = None

        # Listeners
        self._listeners:  list = []

        # Repositories
        self.notification_repo: Optional[NotificationRepository] = None
        
        # Mappers
        self.notification_mapper: Optional[NotificationMapper] = None
        
        # Services
        self.email_service:      Optional[EmailService]         = None
        self.template_service:   Optional[TemplateService]      = None
        self.notification_service: Optional[NotificationService] = None

        # Tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

    # ============================================================= lifespan
    async def startup(self) -> None:
        try:
            self.logger.info("Starting service components...")
            await self._init_messaging()
            await self._init_database()
            self._init_repositories()
            self._init_mappers()
            self._init_local_services()
            await self._init_listeners()
            self.logger.info("%s started successfully", self.config.service_name)
        except Exception:
            self.logger.critical("Service failed to start", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        self.logger.info("Shutting down %s", self.config.service_name)

        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        for lst in self._listeners:
            await lst.stop()

        if self.messaging_client:
            await self.messaging_client.close()
        if self.db_manager:
            await self.db_manager.close()

        self.logger.info("%s shutdown complete", self.config.service_name)

    # ====================================================== init helpers
    async def _init_messaging(self) -> None:
        self.messaging_client = JetStreamClient(self.logger)
        
        await self.messaging_client.connect([self.config.infrastructure_nats_url])
        
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])
        
        self.email_send_publisher = EmailSendPublisher(self.messaging_client, self.logger)
        
        self.logger.info("Messaging client and publisher initialized")

    # ------------------------------------------------------------------ DB
    async def _init_database(self) -> None:
        if not (self.config.db_enabled and self.config.database_config):
            self.logger.warning("DB disabled; repositories will not be initialised")
            return

        self.db_manager = DatabaseSessionManager(
            database_url=self.config.database_config.database_url,
            echo=self.config.database_config.DB_ECHO,
            pool_size=self.config.database_config.DB_POOL_SIZE,
            max_overflow=self.config.database_config.DB_MAX_OVERFLOW,
        )
        await self.db_manager.init()
        set_database_manager(self.db_manager)
        self.logger.info("Connected to DB")

        from shared.database.base import Base
        async with self.db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # ---------------------------------------------------------------- repos
    def _init_repositories(self) -> None:
        if not self.db_manager:
            return
        self.notification_repo = NotificationRepository(
            Notification,
            self.db_manager.session_factory,
        )

    
    def _init_mappers(self) -> None:
        """Initialize mappers"""
        self.notification_mapper = NotificationMapper()
        self.logger.info("Notification mappers initialized")
        
    
    # ---------------------------------------------------------- local services
    def _init_local_services(self) -> None:
        self.email_service = EmailService(
            {
                "primary_provider":  self.config.email_primary_provider,
                "fallback_provider": self.config.email_fallback_provider,
                "sendgrid_config":   {},
                "ses_config":        {},
                "smtp_config":       {},
            },
            self.logger,
        )

        self.template_service = TemplateService(self.config, self.logger)

        if not (self.messaging_client and self.email_send_publisher and self.notification_repo):
            raise RuntimeError("Messaging or DB not initialised")
        
        if not self.notification_mapper:
            raise RuntimeError("Notification mapper not initialized")

        self.notification_service = NotificationService(
            config=self.config,
            email_service=self.email_service,
            template_service=self.template_service,
            notification_repository=self.notification_repo,
            notification_mapper= self.notification_mapper,
            logger=self.logger,
        )

    # -------------------------------------------------------------- listeners
    async def _init_listeners(self) -> None:
        if not (self.messaging_client and self.notification_service and self.email_send_publisher):
            raise RuntimeError("Messaging or service layer not ready")

        email_listener = SendEmailListener(
            js_client=self.messaging_client,
            publisher=self.email_send_publisher,
            svc=self.notification_service,
            logger=self.logger,
        )
        bulk_listener = SendBulkEmailListener(
            js_client=self.messaging_client,
            publisher=self.email_send_publisher,
            svc=self.notification_service,
            logger=self.logger,
        )

        await email_listener.start()
        await bulk_listener.start()
        self._listeners.extend([email_listener, bulk_listener])

    # ================================================= convenience helpers
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        self._shutdown_event.set()
