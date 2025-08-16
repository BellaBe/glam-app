================
# services/catalog-analysis/src/lifecycle.py
================
from contextlib import asynccontextmanager
from typing import Optional, List
import asyncio
import redis.asyncio as redis

from shared.messaging import JetStreamWrapper
from shared.utils.logger import create_logger
from .config import CatalogAnalysisConfig
from .services.catalog_analysis_service import CatalogAnalysisService
from .events.publishers import CatalogAnalysisEventPublisher
from .events.subscribers import CatalogItemAnalysisSubscriber

class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: CatalogAnalysisConfig):
        self.config = config
        self.logger = create_logger(config.service_name)
        
        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Services
        self.catalog_analysis_service: Optional[CatalogAnalysisService] = None
        
        # Event handling
        self.event_publisher: Optional[CatalogAnalysisEventPublisher] = None
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
    
    async def startup(self) -> None:
        """Initialize all components in order"""
        self.logger.info(f"Starting {self.config.service_name}")
        
        # 1. Redis
        self.redis_client = await redis.from_url(
            self.config.infrastructure_redis_url,
            encoding="utf-8"
        )
        
        # 2. Messaging
        self.messaging_wrapper = JetStreamWrapper(self.logger)
        await self.messaging_wrapper.connect(self.config.nats_servers)
        
        # 3. Create publisher
        self.event_publisher = self.messaging_wrapper.create_publisher(CatalogAnalysisEventPublisher)
        
        # 4. Initialize services
        self.catalog_analysis_service = CatalogAnalysisService(
            config=self.config,
            logger=self.logger
        )
        
        # 5. Register dependencies for subscribers
        self.messaging_wrapper.register_dependency("catalog_analysis_service", self.catalog_analysis_service)
        self.messaging_wrapper.register_dependency("publisher", self.event_publisher)
        self.messaging_wrapper.register_dependency("logger", self.logger)
        
        # 6. Start event subscribers
        await self.messaging_wrapper.start_subscriber(CatalogItemAnalysisSubscriber)
        
        self.logger.info(f"✅ {self.config.service_name} started successfully")
    
    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info(f"Shutting down {self.config.service_name}")
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Close connections
        if self.messaging_wrapper:
            await self.messaging_wrapper.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info(f"✅ {self.config.service_name} shutdown complete")