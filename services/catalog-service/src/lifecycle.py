# src/lifecycle.py
from contextlib import asynccontextmanager
from typing import Optional, List
import asyncio
import redis.asyncio as redis
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging import JetStreamWrapper
from shared.utils.logger import create_logger
from .config import CatalogServiceConfig
from .repositories.item_repository import ItemRepository
from .repositories.sync_operation_repository import SyncOperationRepository
from .repositories.analysis_result_repository import AnalysisResultRepository
from .mappers.sync_operation_mapper import SyncOperationMapper
from .mappers.item_mapper import ItemMapper
from .services.sync_service import SyncService
from .services.catalog_service import CatalogService
from .events.publishers import CatalogEventPublisher
from .events.subscribers import ProductsFetchedSubscriber, AnalysisCompletedSubscriber

class CatalogServiceLifecycle:
    """Manages catalog service lifecycle and dependencies"""
    
    def __init__(self, config: CatalogServiceConfig):
        self.config = config
        self.logger = create_logger(config.service_name)
        
        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Repositories
        self.item_repo: Optional[ItemRepository] = None
        self.sync_repo: Optional[SyncOperationRepository] = None
        self.analysis_repo: Optional[AnalysisResultRepository] = None
        
        # Mappers
        self.sync_mapper: Optional[SyncOperationMapper] = None
        self.item_mapper: Optional[ItemMapper] = None
        
        # Services
        self.sync_service: Optional[SyncService] = None
        self.catalog_service: Optional[CatalogService] = None
        
        # Event handling
        self.event_publisher: Optional[CatalogEventPublisher] = None
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
    
    async def startup(self) -> None:
        """Initialize all components in order"""
        self.logger.info(f"Starting {self.config.service_name}")
        
        # 1. Database
        if self.config.db_enabled:
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
        self.event_publisher = self.messaging_wrapper.create_publisher(CatalogEventPublisher)
        
        # 5. Initialize repositories
        if self.db_manager:
            self.item_repo = ItemRepository(self.db_manager.session_factory)
            self.sync_repo = SyncOperationRepository(self.db_manager.session_factory)
            self.analysis_repo = AnalysisResultRepository(self.db_manager.session_factory)
        
        # 6. Initialize mappers
        self.sync_mapper = SyncOperationMapper()
        self.item_mapper = ItemMapper()
        
        # 7. Initialize services
        self.sync_service = SyncService(
            sync_repo=self.sync_repo,
            item_repo=self.item_repo,
            mapper=self.sync_mapper,
            publisher=self.event_publisher,
            redis_client=self.redis_client,
            logger=self.logger,
            config=self.config
        )
        
        self.catalog_service = CatalogService(
            item_repo=self.item_repo,
            analysis_repo=self.analysis_repo,
            item_mapper=self.item_mapper,
            publisher=self.event_publisher,
            logger=self.logger,
            config=self.config
        )
        
        # 8. Register dependencies for subscribers
        self.messaging_wrapper.register_dependency("catalog_service", self.catalog_service)
        self.messaging_wrapper.register_dependency("logger", self.logger)
        
        # 9. Start event subscribers
        await self.messaging_wrapper.start_subscriber(ProductsFetchedSubscriber)
        await self.messaging_wrapper.start_subscriber(AnalysisCompletedSubscriber)
        
        # 10. Start background tasks
        if self.config.startup_recovery_enabled:
            task = asyncio.create_task(self._recovery_task())
            self._tasks.append(task)
    
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
    
    async def _recovery_task(self):
        """Background recovery task"""
        try:
            # Initial recovery scan
            await self.catalog_service.recovery_scan()
            
            # Periodic reconciliation
            while True:
                await asyncio.sleep(self.config.reconciliation_interval_min * 60)
                await self.catalog_service.recovery_scan()
                
        except asyncio.CancelledError:
            self.logger.info("Recovery task cancelled")
        except Exception as e:
            self.logger.error(f"Recovery task failed: {e}")