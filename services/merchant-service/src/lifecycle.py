# services/merchant-service/src/lifecycle.py
from contextlib import asynccontextmanager
from typing import Optional, List
import asyncio
import redis.asyncio as redis
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_wrapper import JetStreamWrapper
from shared.utils.logger import ServiceLogger
from .config import MerchantServiceConfig
from .repositories import MerchantRepository
from .services import MerchantService
from .mappers import MerchantMapper
from .events.publishers import MerchantEventPublisher
from .events.subscribers import WebhookAppInstalledSubscriber, BillingSubscriptionActivatedSubscriber

class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: MerchantServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Repositories
        self.merchant_repo: Optional[MerchantRepository] = None
        
        # Mappers
        self.merchant_mapper: Optional[MerchantMapper] = None
        
        # Services
        self.merchant_service: Optional[MerchantService] = None
        
        # Event handling
        self.event_publisher: Optional[MerchantEventPublisher] = None
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
    
    async def startup(self) -> None:
        """Initialize all components in order"""
        self.logger.info(f"Starting {self.config.service_name}")
        
        # 1. Database
        self.db_manager = DatabaseSessionManager(
            database_url=self.config.database_config.database_url,
            echo=self.config.debug
        )
        await self.db_manager.init()
        set_database_manager(self.db_manager)
        
        # 2. Redis
        self.redis_client = await redis.from_url(
            self.config.infrastructure_redis_url,
            encoding="utf-8"
        )
        
        # 3. Messaging
        self.messaging_wrapper = JetStreamWrapper(self.logger)
        await self.messaging_wrapper.connect(self.config.nats_servers)
        
        # 4. Create publisher
        self.event_publisher = self.messaging_wrapper.create_publisher(MerchantEventPublisher)
        
        # 5. Initialize repositories
        self.merchant_repo = MerchantRepository(self.db_manager.session_factory)
        
        # 6. Initialize mappers
        self.merchant_mapper = MerchantMapper()
        
        # 7. Initialize services
        self.merchant_service = MerchantService(
            config=self.config,
            merchant_repo=self.merchant_repo,
            mapper=self.merchant_mapper,
            publisher=self.event_publisher,
            redis_client=self.redis_client,
            logger=self.logger
        )
        
        # 8. Register dependencies for subscribers
        self.messaging_wrapper.register_dependency("merchant_service", self.merchant_service)
        self.messaging_wrapper.register_dependency("logger", self.logger)
        
        # 9. Start event subscribers
        await self.messaging_wrapper.start_subscriber(WebhookAppInstalledSubscriber)
        await self.messaging_wrapper.start_subscriber(BillingSubscriptionActivatedSubscriber)
    
    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info(f"Shutting down {self.config.service_name}")
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Close connections
        if self.messaging_wrapper:
            await self.messaging_wrapper.close()
        if self.db_manager:
            await self.db_manager.close()
        if self.redis_client:
            await self.redis_client.close()
