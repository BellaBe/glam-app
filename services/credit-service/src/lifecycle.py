"""
Service lifecycle management for credit service.

Manages startup and shutdown of all service components following
the same pattern as notification service.
"""

from __future__ import annotations

import asyncio
from typing import Optional, List, cast

import redis.asyncio as redis
from nats.js.api import StreamConfig, RetentionPolicy, StorageType

from shared.utils.logger import ServiceLogger
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .config import CreditServiceConfig
from .services.credit_service import CreditService
from .services.balance_monitor_service import BalanceMonitorService
from .services.plugin_status_service import PluginStatusService
from .services.credit_transaction_service import CreditTransactionService

# Repositories
from .repositories.credit_repository import CreditRepository
from .repositories.credit_transaction_repository import CreditTransactionRepository

# Models
from .models.credit import Credit
from .models.credit_transaction import CreditTransaction

# Events
from .events.publishers import CreditEventPublisher
from .events.subscribers import (
    OrderUpdatedSubscriber,
    TrialCreditsSubscriber,
    SubscriptionSubscriber,
    MerchantCreatedSubscriber,
    ManualAdjustmentSubscriber
)

# Mappers
from .mappers.credit_mapper import CreditMapper
from .mappers.credit_transaction_mapper import CreditTransactionMapper


class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: CreditServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.redis_client: Optional[redis.Redis] = None
        
        
        # Repositories
        self.credit_repo: Optional[CreditRepository] = None
        self.credit_transaction_repo: Optional[CreditTransactionRepository] = None
        
        # Mappers
        self.credit_mapper: Optional[CreditMapper] = None
        self.credit_transaction_mapper: Optional[CreditTransactionMapper] = None
        
        # Services
        self.credit_service: Optional[CreditService] = None
        self.balance_monitor_service: Optional[BalanceMonitorService] = None
        self.plugin_status_service: Optional[PluginStatusService] = None
        self.credit_transaction_service: Optional[CreditTransactionService] = None
        
        
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
    
    async def _init_messaging(self) -> None:
        self.messaging_wrapper = JetStreamWrapper(self.logger)
        await self.messaging_wrapper.connect(self.config.NATS_SERVERS)
        self.logger.info("Connected to NATS %s", self.config.NATS_SERVERS)

        js = self.messaging_wrapper.js
        cfg = StreamConfig(
            name      = "CREDIT",
            subjects  = ["cmd.credit.*", "evt.credit.*"],
            retention = RetentionPolicy.LIMITS,
            max_age   = 7 * 24 * 60 * 60,
            max_msgs  = 1_000_000,
            max_bytes = 1_024 ** 3,
            storage   = StorageType.FILE,
            duplicate_window = 60,
        )
        try:
            await js.stream_info("CREDIT")
        except Exception:
            await js.add_stream(cfg)
            self.logger.info("Created CREDIT stream")
    
  
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
        """Initialize repositories"""
        
        if not self.db_manager:
            self.logger.warning("DB manager not initialized, repositories will not be set up")
            return
        
        self.logger.info("Setting up repositories...")
        
        session_factory = self.db_manager.session_factory
        
        self.credit_repo = CreditRepository(
            model_class=Credit,
            session_factory=session_factory
        )
        self.credit_transaction_repo = CreditTransactionRepository(
            model_class=CreditTransaction,
            session_factory=session_factory
        )
        
        self.logger.info("Repositories setup complete")
    
    async def _init_redis(self) -> None:
        """Initialize Redis connection"""
        
        self.logger.info("Setting up Redis...")
        
        if not self.config.REDIS_URL:
            self.logger.warning("REDIS_URL not configured, skipping Redis setup")
            return
        
        self.redis_client = redis.from_url(
            self.config.REDIS_URL,
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
        
        self.credit_mapper = CreditMapper()
        self.credit_transaction_mapper = CreditTransactionMapper()
        
        self.logger.info("Mappers setup complete")
    
    
    
    def _init_local_services(self) -> None:
        """Initialize business services"""
        
        self.logger.info("Setting up services...")
        
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper is not initialized")
        
        event_publisher = cast(CreditEventPublisher, 
            self.messaging_wrapper.create_publisher(CreditEventPublisher)
        )
        
        
        # Balance monitor service
        self.balance_monitor_service = BalanceMonitorService(
            config=self.config,
            publisher=event_publisher,
            logger=self.logger
        )
        
        if not self.credit_repo:
            raise RuntimeError("Credit repository is not initialized")
        
        if not self.credit_transaction_repo:
            raise RuntimeError("Credit transaction repository is not initialized")
        
        if not self.redis_client:
            raise RuntimeError("Redis client is not initialized")
        
        if not self.credit_mapper:
            raise RuntimeError("CreditMapper is not initialized")
        
        # Plugin status service
        self.plugin_status_service = PluginStatusService(
            config=self.config,
            credit_repo=self.credit_repo,
            redis_client=self.redis_client,
            logger=self.logger
        )
        
        # Main credit service
        self.credit_service = CreditService(
            config=self.config,
            credit_repo=self.credit_repo,
            publisher=event_publisher,
            balance_monitor=self.balance_monitor_service,
            credit_mapper=self.credit_mapper,
            logger=self.logger
        )
        
        if not self.credit_service:
            raise RuntimeError("CreditService initialization failed")
        if not self.credit_transaction_repo:
            raise RuntimeError("CreditTransactionRepository not initialized")
        if not self.credit_transaction_mapper:
            raise RuntimeError("CreditTransactionMapper not initialized")

        self.credit_transaction_service = CreditTransactionService(
            transaction_repo=self.credit_transaction_repo,
            transaction_mapper=self.credit_transaction_mapper,
            credit_service=self.credit_service,
            logger=self.logger
        )
        
        self.logger.info("Services setup complete")
    
    
    
    async def _init_subscribers(self) -> None:
        """Start event subscribers"""
        
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper is not initialized, cant start subscribers")

        subscribers = [
            OrderUpdatedSubscriber,
            TrialCreditsSubscriber,
            SubscriptionSubscriber,
            MerchantCreatedSubscriber,
            ManualAdjustmentSubscriber
        ]
        
        for sub_cls in subscribers:
            await self.messaging_wrapper.start_subscriber(sub_cls)

    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        self._shutdown_event.set()