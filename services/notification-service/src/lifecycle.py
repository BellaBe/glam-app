# services/notification_service/src/lifecycle.py
"""
Process-wide lifecycle manager for the Notification Service.

• Connects to NATS / JetStream and ensures NOTIFICATION stream exists
• Opens async SQLAlchemy engine and auto-creates tables
• Builds repositories (DB-backed) + their services
• Instantiates NotificationService with all dependencies
• Starts JetStream subscribers as background tasks
• Cleans everything up on shutdown
"""

from __future__ import annotations

import asyncio
from typing import List, Optional, cast

from nats.js.api import StreamConfig, RetentionPolicy, StorageType

from shared.utils.logger import ServiceLogger
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .config import ServiceConfig
from .services.email_service import EmailService
from .services.notification_service import NotificationService
from .services.template_service   import TemplateService

# repositories --------------------------------------------------------------
from .repositories.notification_repository import NotificationRepository


# models ----------------------------------------------------------------
from .models.notification import Notification

# events / subs -------------------------------------------------------------
from .events.publishers import NotificationEventPublisher
from .events.subscribers   import SendEmailSubscriber, SendBulkEmailSubscriber

# domain mappers --------------------------------------------------------
from .mappers.notification_mapper import NotificationMapper


class ServiceLifecycle:
    """Owns singletons that must exist exactly once per process."""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger) -> None:
        self.config = config
        self.logger = logger

        # external connections
        self.messaging_wrapper: Optional[JetStreamWrapper]        = None
        self.db_manager:        Optional[DatabaseSessionManager]  = None

        # repositories
        self.notification_repo: Optional[NotificationRepository] = None

        # utils / domain services
        self.email_service:       Optional[EmailService]              = None
        self.template_service:    Optional[TemplateService]           = None
        self.notification_service:Optional[NotificationService]     = None
        self.notification_mapper: Optional[NotificationMapper] = None

        # bookkeeping
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

    # ─────────────────────────── FastAPI lifespan hooks ────────────────────
    async def startup(self) -> None:
        try:
            await self._init_messaging()
            await self._init_database()
            self._init_repositories()
            self._init_local_services()
            await self._start_subscribers()
            self.logger.info("%s started successfully", self.config.SERVICE_NAME)
        except Exception:
            self.logger.critical("Service failed to start")
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        self.logger.info("Shutting down %s", self.config.SERVICE_NAME)

        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        if self.messaging_wrapper:
            await self.messaging_wrapper.close()
        if self.db_manager:
            await self.db_manager.close()

        self.logger.info("%s shutdown complete", self.config.SERVICE_NAME)

    # ───────────────────────────── init helpers ────────────────────────────
    async def _init_messaging(self) -> None:
        self.messaging_wrapper = JetStreamWrapper(self.logger)
        await self.messaging_wrapper.connect(self.config.NATS_SERVERS)
        self.logger.info("Connected to NATS %s", self.config.NATS_SERVERS)

        js = self.messaging_wrapper.js
        cfg = StreamConfig(
            name      = "NOTIFICATION",
            subjects  = ["cmd.notification.*", "evt.notification.*"],
            retention = RetentionPolicy.LIMITS,
            max_age   = 7 * 24 * 60 * 60,
            max_msgs  = 1_000_000,
            max_bytes = 1_024 ** 3,
            storage   = StorageType.FILE,
            duplicate_window = 60,
        )
        try:
            await js.stream_info("NOTIFICATION")
        except Exception:
            await js.add_stream(cfg)
            self.logger.info("Created NOTIFICATION stream")

    async def _init_database(self) -> None:
        if not (self.config.DB_ENABLED and self.config.database_config):
            self.logger.warning("DB disabled; repositories will not be initialised")
            return

        self.db_manager = DatabaseSessionManager(
            database_url=self.config.database_config.database_url,
            **self.config.database_config.get_engine_kwargs(),
        )
        await self.db_manager.init()
        set_database_manager(self.db_manager)
        self.logger.info("Connected to DB")

        from shared.database.base import Base
        async with self.db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _init_repositories(self) -> None:
        """Create repository singletons (requires DB)."""
        if not self.db_manager:
            return

        sf = self.db_manager.session_factory
        self.notification_repo = NotificationRepository(Notification, sf)

    def _init_local_services(self) -> None:

        self.email_service = EmailService(
            {
                "primary_provider":  self.config.PRIMARY_PROVIDER,
                "fallback_provider": self.config.FALLBACK_PROVIDER,
                "sendgrid_config":   self.config.sendgrid_config.model_dump(),
                "ses_config":        self.config.ses_config.model_dump(),
                "smtp_config":       self.config.smtp_config.model_dump(),
            },
            self.logger,
        )
        
        self.template_service = TemplateService(
            config=self.config,
            logger= self.logger,
        )
    

        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper is not initialized")
        
        publisher = cast(
            NotificationEventPublisher,
            self.messaging_wrapper.create_publisher(NotificationEventPublisher),
        )

        if not self.notification_repo:
            raise RuntimeError("Notification repository is not initialized")
        
        self.notification_service = NotificationService(
            config                  = self.config,
            publisher               = publisher,
            email_service           = self.email_service,
            template_service        = self.template_service,
            notification_repository = self.notification_repo,
            notification_mapper     = NotificationMapper(),
            logger                  = self.logger,
        )

    async def _start_subscribers(self) -> None:
        
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper is not initialized")
        
        subscribers = [
            SendEmailSubscriber,
            SendBulkEmailSubscriber
        ]
        for sub_cls in subscribers:
            await self.messaging_wrapper.start_subscriber(sub_cls)

    # ──────────────────────────── convenience tools ───────────────────────
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        self._shutdown_event.set()
