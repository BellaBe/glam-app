from typing import Optional, List
import asyncio
from prisma import Prisma
import redis.asyncio as redis
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from .config import ServiceConfig
from .repositories.webhook_repository import WebhookRepository
from .services.webhook_service import WebhookService
from .events.publishers import WebhookEventPublisher


class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # External connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.prisma: Optional[Prisma] = None
        self.redis_client: Optional[redis.Redis] = None
        self._db_connected: bool = False
        
        # Publisher / listeners
        self.event_publisher: Optional[WebhookEventPublisher] = None
        self._listeners: list = []
        
        # Repositories / services
        self.webhook_repo: Optional[WebhookRepository] = None
        self.webhook_service: Optional[WebhookService] = None
        
        # Tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
    
    async def startup(self) -> None:
        try:
            self.logger.info("Starting service components...")
            
            await self._init_messaging()
            await self._init_redis()
            await self._init_database()
            self._init_repositories()
            self._init_local_services()
            self.logger.info("%s started successfully", self.config.service_name)
        except Exception:
            self.logger.critical("Service failed to start", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info("Shutting down %s", self.config.service_name)
        
        # Cancel tasks
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Stop listeners
        for lst in self._listeners:
            try:
                await lst.stop()
            except Exception:
                self.logger.critical("Listener stop failed", exc_info=True)
        
        # Close messaging
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.critical("Messaging client close failed", exc_info=True)
        
        # Close Redis
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception:
                self.logger.critical("Redis close failed", exc_info=True)
        
        # Disconnect database
        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.critical("Prisma disconnect failed", exc_info=True)
        
        self.logger.info("%s shutdown complete", self.config.service_name)
    
    async def _init_messaging(self) -> None:
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.>", "cmd.>"])
        
        # Initialize publisher
        self.event_publisher = WebhookEventPublisher(
            jetstream_client=self.messaging_client,
            logger=self.logger,
        )
        
        self.logger.info("Messaging client and publisher initialized")
    
    async def _init_redis(self) -> None:
        """Initialize Redis client"""
        self.redis_client = redis.from_url(
            self.config.redis_url,
            decode_responses=False  # We want bytes for idempotency keys
        )
        
        # Test connection
        await self.redis_client.ping()
        self.logger.info("Redis connected")
    
    async def _init_database(self) -> None:
        """Initialize Prisma client if database is enabled."""
        if not self.config.database_enabled:
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
    
    def _init_repositories(self) -> None:
        if self.config.database_enabled:
            if not (self.prisma and self._db_connected):
                raise RuntimeError("Prisma client not initialized/connected")
            
            self.webhook_repo = WebhookRepository(self.prisma)
            self.logger.info("Webhook repository initialized")
        else:
            self.webhook_repo = None

    
    def _init_local_services(self) -> None:
        """Initialize local services with proper dependencies"""
        if not self.webhook_repo:
            raise RuntimeError("Webhook repository not initialized")
        if not self.event_publisher:
            raise RuntimeError("Event publisher not initialized")
        
        # Initialize webhook service with all required dependencies
        self.webhook_service = WebhookService(
            config=self.config,
            repository=self.webhook_repo,
            publisher=self.event_publisher,
            logger=self.logger
        )
        
        self.logger.info("Services initialized")
    
    
    # Convenience helpers
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t
    
    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()
    
    def signal_shutdown(self) -> None:
        self._shutdown_event.set()


