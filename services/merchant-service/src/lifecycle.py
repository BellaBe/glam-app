# services/merchant-service/src/lifecycle.py
from __future__ import annotations

import asyncio
from typing import List, Optional, cast
import redis.asyncio as redis
from nats.js.api import StreamConfig, RetentionPolicy, StorageType

from shared.utils.logger import ServiceLogger
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .config import MerchantServiceConfig
from .repositories import (
    
)
from .services import (
   
)
from .events import BillingEventPublisher

from .subscribers import (
   
)
from .mappers import (
   
)

from .models import (
   
)

from .exceptions import MerchantServiceError




class ServiceLifecycle:
    """Manages merchant service lifecycle and dependencies"""

    def __init__(self, config: MerchantServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Repositories

        # External services

        
        # Services

        
        # Mappers

        
        # Event handling

        # bookkeeping
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
            
            # 7. Start subscribers
            await self._init_subscribers()
            
            self.logger.info("All service components started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Shutdown all service components"""
        
        self.logger.info("Shutting down service components...")
        
        # Stop background tasks
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Close Redis
        if self.redis_client:
            try:
                await self.redis_client.close()
                self.logger.info("Redis connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing Redis: {e}")
        
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
                self.logger.warning(f"Error closing database: {e}")
        
        self.logger.info("Service shutdown complete")
        """Graceful shutdown of all components"""
        self.logger.info(f"Shutting down {self.config.service_name}")
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Close connections
        if self.messaging:
            await self.messaging.close()
        if self.db_manager:
            await self.db_manager.close()
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info(f"{self.config.service_name} shutdown complete")
        
    async def _init_messaging(self) -> None:
        self.messaging_wrapper = JetStreamWrapper(self.logger)
        await self.messaging_wrapper.connect([self.config.infrastructure_nats_url])
        self.logger.info("Connected to NATS %s", self.config.infrastructure_nats_url)

        js = self.messaging_wrapper.js
        cfg = StreamConfig(
            name      = "MERCHANT",
            subjects  = ["cmd.merchant.*", "evt.merchant.*"],
            retention = RetentionPolicy.LIMITS,
            max_age   = 7 * 24 * 60 * 60,
            max_msgs  = 1_000_000,
            max_bytes = 1_024 ** 3,
            storage   = StorageType.FILE,
            duplicate_window = 60,
        )
        try:
            await js.stream_info("MERCHANT")
        except Exception:
            await js.add_stream(cfg)
            self.logger.info("Created MERCHANT stream")

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
    
    
    def _init_repositories(self) -> None:
        """Initialize repositories"""
        
        if not self.db_manager:
            self.logger.warning("DB manager not initialized, repositories will not be set up")
            return
        
        self.logger.info("Setting up repositories...")
        
        session_factory = self.db_manager.session_factory
        
        
        self.logger.info("Repositories initialized successfully")
        
    def _init_mappers(self) -> None:
        """Initialize mappers"""
        
        self.logger.info("Setting up mappers...")
        
        
        self.logger.info("Mappers initialized successfully")
        
    async def _init_subscribers(self) -> None:
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper not initialized")

        # ⚠️ Register deps BEFORE launching subscribers – they may receive a
        # message immediately after pull_subscribe().
        
        self.messaging_wrapper.register_dependency("logger", self.logger)
        
        # Start all subscribers with registered dependencies
        subscribers = [
            WebhookEventSubscriber,
            PurchaseWebhookSubscriber,
            AppUninstalledSubscriber,
        ]
        
        for subscriber_class in subscribers:
            await self.messaging_wrapper.start_subscriber(subscriber_class)
        
        
    def _init_local_services(self) -> None:
        """Initialize local services"""
        
        self.logger.info("Setting up local services...")
       
        
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper is not initialized")

        self.event_publisher = cast(MerchantEventPublisher, self.messaging_wrapper.create_publisher(MerchantEventPublisher))
        
        if not self.event_publisher:
            raise RuntimeError("Event publisher is not initialized")
        
        if not self.redis_client:
            raise RuntimeError("Redis client is not initialized")

       

        # Initialize services with dependencies
        self.logger.info("Initializing local services...")
        
       
        
        self.logger.info("Local services initialized successfully")
        
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        self._shutdown_event.set()