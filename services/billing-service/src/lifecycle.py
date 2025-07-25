# services/billing-service/src/lifecycle.py
from __future__ import annotations

import asyncio
from typing import List, Optional, cast
import redis.asyncio as redis
from nats.js.api import StreamConfig, RetentionPolicy, StorageType

from shared.utils.logger import ServiceLogger
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_client import JetStreamWrapper

from .config import BillingServiceConfig
from .repositories import (
    SubscriptionRepository,
    OneTimePurchaseRepository,
    BillingPlanRepository,
    TrialExtensionRepository,
)
from .services import (
    BillingService,
    TrialService,
    OneTimePurchaseService,
)
from .events import BillingEventPublisher
from .clients.shopify import ShopifyBillingClient
from .subscribers import (
    WebhookEventSubscriber,
    PurchaseWebhookSubscriber,
    AppUninstalledSubscriber,
)
from .mappers import (
    BillingPlanMapper,
    SubscriptionMapper,
    OneTimePurchaseMapper,
    TrialExtensionMapper,
)

from .models import (
    Subscription,
    OneTimePurchase,
    BillingPlan,
    TrialExtension,
)

from .exceptions import BillingServiceError




class ServiceLifecycle:
    """Manages billing service lifecycle and dependencies"""

    def __init__(self, config: BillingServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger

        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Repositories
        self.subscription_repo: Optional[SubscriptionRepository] = None
        self.purchase_repo: Optional[OneTimePurchaseRepository] = None
        self.plan_repo: Optional[BillingPlanRepository] = None
        self.extension_repo: Optional[TrialExtensionRepository] = None
        
        # External services
        self.shopify_client: Optional[ShopifyBillingClient] = None
        
        # Services
        self.billing_service: Optional[BillingService] = None
        self.trial_service: Optional[TrialService] = None
        self.purchase_service: Optional[OneTimePurchaseService] = None
        
        # Mappers
        self.plan_mapper: BillingPlanMapper = BillingPlanMapper()
        self.subscription_mapper: SubscriptionMapper = SubscriptionMapper()
        self.purchase_mapper: OneTimePurchaseMapper = OneTimePurchaseMapper()
        self.extension_mapper: TrialExtensionMapper = TrialExtensionMapper()
        
        # Event handling
        self.event_publisher: Optional[BillingEventPublisher] = None
        
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
            name      = "BILLING",
            subjects  = ["cmd.billing.*", "evt.billing.*"],
            retention = RetentionPolicy.LIMITS,
            max_age   = 7 * 24 * 60 * 60,
            max_msgs  = 1_000_000,
            max_bytes = 1_024 ** 3,
            storage   = StorageType.FILE,
            duplicate_window = 60,
        )
        try:
            await js.stream_info("BILLING")
        except Exception:
            await js.add_stream(cfg)
            self.logger.info("Created BILLING stream")
    
  
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
        
        self.subscription_repo = SubscriptionRepository(
            model_class=Subscription,
            session_factory=session_factory
        )
        self.purchase_repo = OneTimePurchaseRepository(
            model_class=OneTimePurchase,
            session_factory=session_factory
        )
        self.plan_repo = BillingPlanRepository(
            model_class=BillingPlan,
            session_factory=session_factory
        )
        self.extension_repo = TrialExtensionRepository(
            model_class=TrialExtension,
            session_factory=session_factory
        )
        self.logger.info("Repositories initialized successfully")
        
    def _init_mappers(self) -> None:
        """Initialize mappers"""
        
        self.logger.info("Setting up mappers...")
        
        self.plan_mapper = BillingPlanMapper()
        self.subscription_mapper = SubscriptionMapper()
        self.purchase_mapper = OneTimePurchaseMapper()
        self.extension_mapper = TrialExtensionMapper()
        
        self.logger.info("Mappers initialized successfully")
        
    async def _init_subscribers(self) -> None:
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper not initialized")

        # ⚠️ Register deps BEFORE launching subscribers – they may receive a
        # message immediately after pull_subscribe().
        self.messaging_wrapper.register_dependency(
            "subscription_repo", self.subscription_repo
        )
        self.messaging_wrapper.register_dependency(
            "purchase_repo", self.purchase_repo
        )
        self.messaging_wrapper.register_dependency(
            "plan_repo", self.plan_repo
        )
        self.messaging_wrapper.register_dependency(
            "extension_repo", self.extension_repo
        )
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
        
        self.shopify_client = ShopifyBillingClient(
            api_key=self.config.shopify_api_key,
            api_secret=self.config.shopify_api_secret,
            app_url=self.config.shopify_app_url,
            logger=self.logger
        )
        
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper is not initialized")
        
        self.event_publisher = cast(BillingEventPublisher, self.messaging_wrapper.create_publisher(BillingEventPublisher))
        
        if not self.event_publisher:
            raise RuntimeError("Event publisher is not initialized")
        
        if not self.redis_client:
            raise RuntimeError("Redis client is not initialized")

        if not self.subscription_repo:
            raise RuntimeError("Subscription repository is not initialized")
        
        if not self.plan_repo:
            raise RuntimeError("Billing plan repository is not initialized")
        
        if not self.purchase_repo:
            raise RuntimeError("One-time purchase repository is not initialized")
        
        if not self.extension_repo:
            raise RuntimeError("Trial extension repository is not initialized")
        
        if not self.shopify_client:
            raise RuntimeError("Shopify client is not initialized")

        # Initialize services with dependencies
        self.logger.info("Initializing local services...")
        
        self.billing_service = BillingService(
            subscription_repo=self.subscription_repo,
            plan_repo=self.plan_repo,
            shopify_client=self.shopify_client,
            event_publisher=self.event_publisher,
            redis_client=self.redis_client,
            logger=self.logger,
            config=self.config
        )
        
        self.trial_service = TrialService(
            extension_repo=self.extension_repo,
            event_publisher=self.event_publisher,
            logger=self.logger,
            config=self.config
        )
        
        self.purchase_service = OneTimePurchaseService(
            purchase_repo=self.purchase_repo,
            event_publisher=self.event_publisher,
            shopify_client=self.shopify_client,
            logger=self.logger,
            config=self.config
        )
        
        self.logger.info("Local services initialized successfully")
        
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        self._shutdown_event.set()