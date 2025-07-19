# services/billing-service/src/lifecycle.py
from contextlib import asynccontextmanager
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging import JetStreamWrapper
from shared.utils.logger import create_logger
from typing import Optional, List
import asyncio
import redis.asyncio as redis


class BillingServiceLifecycle:
    """Manages billing service lifecycle and dependencies"""
    
    def __init__(self, config: BillingServiceConfig):
        self.config = config
        self.logger = create_logger(config.service_name)
        
        # External connections
        self.messaging = JetStreamWrapper(self.logger)
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
        
        # Event handling
        self.event_publisher: Optional[BillingEventPublisher] = None
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
    
    async def startup(self) -> None:
        """Initialize all components in order"""
        self.logger.info(f"Starting {self.config.service_name}")
        
        # 1. Database
        self.db_manager = DatabaseSessionManager(
            database_url=self.config.database_url,
            echo=self.config.debug
        )
        await self.db_manager.init()
        set_database_manager(self.db_manager)
        
        # 2. Redis
        self.redis_client = await redis.from_url(
            self.config.redis_url,
            encoding="utf-8"
        )
        
        # 3. Messaging
        await self.messaging.connect(self.config.nats_servers)
        
        # 4. Create publisher
        self.event_publisher = self.messaging.create_publisher(BillingEventPublisher)
        
        # 5. Initialize repositories
        self.subscription_repo = SubscriptionRepository(self.db_manager.session_factory)
        self.purchase_repo = OneTimePurchaseRepository(self.db_manager.session_factory)
        self.plan_repo = BillingPlanRepository(self.db_manager.session_factory)
        self.extension_repo = TrialExtensionRepository(self.db_manager.session_factory)
        
        # 6. Initialize external services
        self.shopify_client = ShopifyBillingClient(
            api_key=self.config.shopify_api_key.get_secret_value() if self.config.shopify_api_key else "",
            api_secret=self.config.shopify_api_secret.get_secret_value() if self.config.shopify_api_secret else ""
        )
        
        # 7. Initialize services
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
            shopify_client=self.shopify_client,
            event_publisher=self.event_publisher,
            logger=self.logger,
            config=self.config
        )
        
        # 8. Register dependencies for subscribers
        self.messaging.register_dependency("billing_service", self.billing_service)
        self.messaging.register_dependency("purchase_service", self.purchase_service)
        self.messaging.register_dependency("logger", self.logger)
        
        # 9. Start event subscribers
        await self.messaging.start_subscriber(WebhookEventSubscriber)
        await self.messaging.start_subscriber(PurchaseWebhookSubscriber)
        await self.messaging.start_subscriber(AppUninstalledSubscriber)
        
        self.logger.info(f"{self.config.service_name} started successfully")
    
    async def shutdown(self) -> None:
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