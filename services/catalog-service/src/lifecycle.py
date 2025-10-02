# services/catalog-service/src/lifecycle.py
from typing import Optional, List
import asyncio
import redis.asyncio as redis
from prisma import Prisma

from shared.messaging import JetStreamClient
from shared.utils.logger import ServiceLogger

from .config import ServiceConfig
from .repositories.catalog_repository import CatalogRepository
from .repositories.sync_repository import SyncRepository
from .repositories.analysis_repository import AnalysisRepository
from .services.catalog_service import CatalogService
from .events.publishers import CatalogEventPublisher
from .events.listeners import ProductsFetchedListener, AnalysisCompletedListener

class ServiceLifecycle:
    """Manages all service components lifecycle"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.prisma: Optional[Prisma] = None
        self.redis: Optional[redis.Redis] = None
        self._db_connected = False
        
        # Components
        self.event_publisher: Optional[CatalogEventPublisher] = None
        self.catalog_repo: Optional[CatalogRepository] = None
        self.sync_repo: Optional[SyncRepository] = None
        self.analysis_repo: Optional[AnalysisRepository] = None
        self.catalog_service: Optional[CatalogService] = None
        
        # Listeners
        self._listeners: List = []
        self._tasks: List[asyncio.Task] = []
    
    async def startup(self) -> None:
        """Initialize all components in correct order"""
        try:
            self.logger.info("Starting catalog service components...")
            
            # 1. Messaging (for events)
            await self._init_messaging()
            
            # 2. Database
            await self._init_database()
            
            # 3. Redis (for progress caching)
            await self._init_redis()
            
            # 4. Repositories (depends on Prisma)
            self._init_repositories()
            
            # 5. Services (depends on repositories)
            self._init_services()
            
            # 6. Event listeners (depends on services)
            await self._init_listeners()
            
            self.logger.info("Catalog service started successfully")
            
        except Exception as e:
            self.logger.critical("Service startup failed", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Graceful shutdown in reverse order"""
        self.logger.info("Shutting down catalog service")
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Stop listeners
        for listener in self._listeners:
            try:
                await listener.stop()
            except Exception:
                self.logger.exception("Listener stop failed", exc_info=True)
        
        # Close Redis
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                self.logger.exception("Redis close failed", exc_info=True)
        
        # Close messaging
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.exception("Messaging close failed", exc_info=True)
        
        # Disconnect database
        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.exception("Prisma disconnect failed", exc_info=True)
        
        self.logger.info("Catalog service shutdown complete")
    
    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream for events"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])
        
        # Initialize publisher
        self.event_publisher = CatalogEventPublisher(
            jetstream_client=self.messaging_client,
            logger=self.logger
        )
        
        self.logger.info("Messaging client and publisher initialized")
    
    async def _init_database(self) -> None:
        """Initialize Prisma client"""
        if not self.config.database_enabled:
            self.logger.info("Database disabled; skipping Prisma initialization")
            return
        
        self.prisma = Prisma()
        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Prisma connected")
        except Exception as e:
            self.logger.exception(f"Prisma connect failed: {e}", exc_info=True)
            raise
    
    async def _init_redis(self) -> None:
        """Initialize Redis for progress caching"""
        if not self.config.redis_enabled:
            self.logger.info("Redis disabled; skipping initialization")
            return
        
        try:
            self.redis = await redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            self.logger.info("Redis connected")
        except Exception as e:
            self.logger.warning(f"Redis connect failed: {e}. Continuing without cache.")
            self.redis = None
    
    def _init_repositories(self) -> None:
        """Initialize repositories with Prisma client"""
        if not self._db_connected:
            self.logger.warning("Database not connected, skipping repositories")
            return
        
        self.catalog_repo = CatalogRepository(self.prisma)
        self.sync_repo = SyncRepository(self.prisma)
        self.analysis_repo = AnalysisRepository(self.prisma)
        
        self.logger.info("Repositories initialized")
    
    def _init_services(self) -> None:
        """Initialize business services"""
        if not self.catalog_repo or not self.sync_repo:
            raise RuntimeError("Repositories not initialized")
        
        self.catalog_service = CatalogService(
            catalog_repo=self.catalog_repo,
            sync_repo=self.sync_repo,
            redis_client=self.redis,
            logger=self.logger,
            config=vars(self.config)
        )
        
        self.logger.info("Catalog service initialized")
    
    async def _init_listeners(self) -> None:
        """Initialize event listeners"""
        if not self.messaging_client or not self.catalog_service:
            raise RuntimeError("Messaging or service not ready")
        
        # Products fetched listener
        products_listener = ProductsFetchedListener(
            js_client=self.messaging_client,
            publisher=self.event_publisher,
            service=self.catalog_service,
            logger=self.logger
        )
        await products_listener.start()
        self._listeners.append(products_listener)
        
        # Analysis completed listener
        analysis_listener = AnalysisCompletedListener(
            js_client=self.messaging_client,
            analysis_repo=self.analysis_repo,
            catalog_repo=self.catalog_repo,
            logger=self.logger
        )
        await analysis_listener.start()
        self._listeners.append(analysis_listener)
        
        self.logger.info("Event listeners started")