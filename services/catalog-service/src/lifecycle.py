from typing import Optional, List
import asyncio
from redis import asyncio as aioredis
from prisma import Prisma
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from .config import ServiceConfig
from .repositories.catalog_state_repository import CatalogStateRepository
from .repositories.sync_job_repository import SyncJobRepository
from .repositories.sync_item_repository import SyncItemRepository
from .services.catalog_sync_service import CatalogSyncService
from .services.cache_service import CacheService
from .events.publishers import CatalogEventPublisher
from .events.listeners import (
    MerchantSettingsListener,
    BillingEntitlementsListener,
    CatalogCountedListener,
    CatalogItemListener,
    AnalysisCompletedListener
)

class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # External connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.prisma: Optional[Prisma] = None
        self._db_connected: bool = False
        self.redis: Optional[aioredis.Redis] = None
        
        # Publisher / listeners
        self.event_publisher: Optional[CatalogEventPublisher] = None
        self._listeners: list = []
        
        # Repositories
        self.catalog_state_repo: Optional[CatalogStateRepository] = None
        self.sync_job_repo: Optional[SyncJobRepository] = None
        self.sync_item_repo: Optional[SyncItemRepository] = None
        
        # Services
        self.cache_service: Optional[CacheService] = None
        self.catalog_sync_service: Optional[CatalogSyncService] = None
        
        # Tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
    
    async def startup(self) -> None:
        try:
            self.logger.info("Starting service components...")
            await self._init_messaging()
            await self._init_database()
            await self._init_redis()
            self._init_repositories()
            self._init_local_services()
            await self._init_listeners()
            self.logger.info("%s started successfully", self.config.service_name)
        except Exception:
            self.logger.critical("Service failed to start", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info("Shutting down %s", self.config.service_name)
        
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        for lst in self._listeners:
            try:
                await lst.stop()
            except Exception:
                self.logger.critical("Listener stop failed")
        
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                self.logger.critical("Redis close failed")
        
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.critical("Messaging client close failed")
        
        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.critical("Prisma disconnect failed")
        
        self.logger.info("%s shutdown complete", self.config.service_name)
    
    async def _init_messaging(self) -> None:
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])
        
        # Initialize publisher now
        self.event_publisher = CatalogEventPublisher(
            messaging=self.messaging_client,
            logger=self.logger,
            config=self.config,
        )
        self.logger.info("Messaging client and publisher initialized")
    
    async def _init_database(self) -> None:
        """Initialize Prisma client if database is enabled."""
        if not self.config.db_enabled:
            self.logger.info("Database disabled; skipping Prisma initialization")
            return
        
        self.prisma = Prisma()
        if not self.prisma:
            raise RuntimeError("Prisma client not initialized")
        
        try:
            await self.prisma.connect()
            self._db_connected = True
            self.logger.info("Prisma connected")
        except Exception as e:
            self.logger.error("Prisma connect failed: %s", e, exc_info=True)
            raise
    
    async def _init_redis(self) -> None:
        """Initialize Redis connection for caching."""
        self.redis = await aioredis.from_url(
            self.config.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis.ping()
        self.logger.info("Redis connected")
    
    def _init_repositories(self) -> None:
        if self.config.db_enabled:
            if not (self.prisma and self._db_connected):
                raise RuntimeError("Prisma client not initialized/connected")
            
            self.catalog_state_repo = CatalogStateRepository(self.prisma)
            self.sync_job_repo = SyncJobRepository(self.prisma)
            self.sync_item_repo = SyncItemRepository(self.prisma)
            self.logger.info("Repositories initialized")
        else:
            self.catalog_state_repo = None
            self.sync_job_repo = None
            self.sync_item_repo = None
    
    def _init_local_services(self) -> None:
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        
        self.cache_service = CacheService(
            redis=self.redis,
            logger=self.logger,
            config=self.config
        )
        
        if not self.catalog_state_repo or not self.sync_job_repo or not self.sync_item_repo:
            raise RuntimeError("Repositories not initialized")
        
        if not self.event_publisher:
            raise RuntimeError("Event publisher not initialized")
        
        self.catalog_sync_service = CatalogSyncService(
            catalog_state_repo=self.catalog_state_repo,
            sync_job_repo=self.sync_job_repo,
            sync_item_repo=self.sync_item_repo,
            event_publisher=self.event_publisher,
            cache_service=self.cache_service,
            logger=self.logger,
            config=self.config
        )
    
    async def _init_listeners(self) -> None:
        if not self.messaging_client:
            raise RuntimeError("Messaging not ready")
        
        # Merchant settings listener
        merchant_listener = MerchantSettingsListener(
            js_client=self.messaging_client,
            cache_service=self.cache_service,
            catalog_state_repo=self.catalog_state_repo,
            logger=self.logger
        )
        await merchant_listener.start()
        self._listeners.append(merchant_listener)
        
        # Billing entitlements listener
        billing_listener = BillingEntitlementsListener(
            js_client=self.messaging_client,
            cache_service=self.cache_service,
            catalog_state_repo=self.catalog_state_repo,
            logger=self.logger
        )
        await billing_listener.start()
        self._listeners.append(billing_listener)
        
        # Catalog counted listener
        counted_listener = CatalogCountedListener(
            js_client=self.messaging_client,
            sync_job_repo=self.sync_job_repo,
            logger=self.logger
        )
        await counted_listener.start()
        self._listeners.append(counted_listener)
        
        # Catalog item listener
        item_listener = CatalogItemListener(
            js_client=self.messaging_client,
            sync_service=self.catalog_sync_service,
            logger=self.logger
        )
        await item_listener.start()
        self._listeners.append(item_listener)
        
        # Analysis completed listener
        analysis_listener = AnalysisCompletedListener(
            js_client=self.messaging_client,
            sync_service=self.catalog_sync_service,
            logger=self.logger
        )
        await analysis_listener.start()
        self._listeners.append(analysis_listener)
        
        self.logger.info("All listeners started")
    
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t
    
    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()
    
    def signal_shutdown(self) -> None:
        self._shutdown_event.set()

# ================================================================
