# services/webhook-service/src/lifecycle.py
"""
Service lifecycle management for webhook service.

Manages startup and shutdown of all service components following
the same pattern as notification and credit services.
"""

from __future__ import annotations

import asyncio
from typing import Optional, List, cast

import redis.asyncio as redis
from nats.js.api import StreamConfig, RetentionPolicy, StorageType

from shared.utils.logger import ServiceLogger
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .config import WebhookServiceConfig
from .services.webhook_service import WebhookService
from .services.platform_handler_service import PlatformHandlerService

# Repositories
from .repositories.webhook_entry_repository import WebhookEntryRepository
from .repositories.platform_configuration_repository import PlatformConfigurationRepository

# Models
from .models.webhook_entry import WebhookEntry
from .models.platform_configuration import PlatformConfiguration

# Events
from .events.publishers import WebhookEventPublisher

# Mappers
from .mappers.webhook_entry_mapper import WebhookEntryMapper


class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: WebhookServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Repositories
        self.webhook_entry_repo: Optional[WebhookEntryRepository] = None
        self.platform_config_repo: Optional[PlatformConfigurationRepository] = None
        
        # Mappers
        self.webhook_entry_mapper: Optional[WebhookEntryMapper] = None
        
        # Services
        self.webhook_service: Optional[WebhookService] = None
        self.platform_handler_service: Optional[PlatformHandlerService] = None
        
        # Publishers
        self.webhook_event_publisher: Optional[WebhookEventPublisher] = None
        
        # Tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

    async def startup(self) -> None:
        """Start all service components"""

        try:
            self.logger.info("Starting service components...")
            
            # 1. Initialize database
            await self._init_database()
            
            # 2. Initialize Redis
            await self._init_redis()
            
            # 3. Initialize messaging
            await self._init_messaging()
            
             # 4. Initialize repositories
            self._init_repositories()
            
            # 5. Initialize mappers
            self._init_mappers()

            # 6. Initialize services
            self._init_local_services()     
            
            self.logger.info("All webhook service components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Cleanup all service components"""
        
        self.logger.info("Shutting down service components...")
        
         # Stop background tasks
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
        # Close Redis
        if self.redis_client:
            try:
                await self.redis_client.aclose()
                self.logger.info("Redis connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Redis connection: {e}")
        
        # Close messaging
        if self.messaging_wrapper:
            try:
                await self.messaging_wrapper.close()
                self.logger.info("Messaging connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing messaging: {e}")
        
        
        # Close database
        if self.db_manager:
            try:
                await self.db_manager.close()
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing database connection: {e}")
        
        self.logger.info("Webhook service shutdown complete")

    
    async def _init_messaging(self) -> None:
        self.messaging_wrapper = JetStreamWrapper(self.logger)
        await self.messaging_wrapper.connect([self.config.infrastructure_nats_url])
        self.logger.info("Connected to NATS %s", self.config.infrastructure_nats_url)

        js = self.messaging_wrapper.js
        cfg = StreamConfig(
            name      = "WEBHOOK",
            subjects  = ["evt.webhook.*"],
            retention = RetentionPolicy.LIMITS,
            max_age   = 7 * 24 * 60 * 60,
            max_msgs  = 1_000_000,
            max_bytes = 1_024 ** 3,
            storage   = StorageType.FILE,
            duplicate_window = 60,
        )
        try:
            await js.stream_info("WEBHOOK")
        except Exception:
            await js.add_stream(cfg)
            self.logger.info("Created WEBHOOK stream")

    
    async def _init_database(self) -> None:
        if not (self.config.db_enabled and self.config.database_config):
            self.logger.warning("DB disabled; repositories will not be initialised")
            return
        
        print("Database URL:", self.config.database_config.database_url)

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
    
    
    def _init_repositories(self) -> None:
        """Initialize repositories"""
        
        if not self.db_manager:
            self.logger.warning("DB manager not initialized, repositories will not be set up")
            return
        
        self.logger.info("Setting up repositories...")
        
        session_factory = self.db_manager.session_factory
        
        self.webhook_entry_repo = WebhookEntryRepository(WebhookEntry, session_factory)
        self.platform_config_repo = PlatformConfigurationRepository(PlatformConfiguration, session_factory)

        self.logger.info("Repositories setup complete")
    
    async def _init_redis(self) -> None:
        """Initialize Redis connection"""
        
        self.logger.info("Setting up Redis...")
        
        if not self.config.infrastructure_redis_url:
            self.logger.warning("INFRASTRUCTURE_REDIS_URL not configured, skipping Redis setup")
            return
        
        self.redis_client = redis.from_url(
            self.config.infrastructure_redis_url,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        await self.redis_client.ping()
        
        self.logger.info("Redis setup complete")
    
    def _init_mappers(self) -> None:
        """Initialize mappers"""
        
        self.logger.info("Setting up mappers...")
        
        self.webhook_entry_mapper = WebhookEntryMapper()
        self.logger.info("Mappers setup complete")

    def _init_local_services(self) -> None:
        """Initialize business services"""
        
        self.logger.info("Setting up services...")
        
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper is not initialized")
        
        publisher = cast(
            WebhookEventPublisher,
            self.messaging_wrapper.create_publisher(WebhookEventPublisher),
        )
        if not self.webhook_entry_repo:
            raise RuntimeError("WebhookEntryRepository is not initialized")
        
        if not self.platform_config_repo:
            raise RuntimeError("PlatformConfigurationRepository is not initialized")
        
        if not self.redis_client:
            raise RuntimeError("Redis client is not initialized")
            
        self.webhook_service = WebhookService(
            webhook_entry_repo=self.webhook_entry_repo,
            platform_config_repo=self.platform_config_repo,
            redis_client=self.redis_client,
            publisher=publisher,
            config=self.config,
            logger=self.logger
        )
        
        self.logger.info("Services setup complete")

    # Convenience methods
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        self._shutdown_event.set()