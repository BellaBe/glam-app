from typing import Optional, List
import asyncio
import redis.asyncio as redis
from prisma import Prisma
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from .config import ServiceConfig
from .repositories.credit_repository import CreditRepository
from .services.credit_service import CreditService
from .events.publishers import CreditEventPublisher
from .events.listeners import BillingCreditGrantListener, BillingTrialActivatedListener

class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # External connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.redis_client: Optional[redis.Redis] = None
        self.prisma: Optional[Prisma] = None
        self._db_connected: bool = False
        
        # Publishers / listeners
        self.event_publisher: Optional[CreditEventPublisher] = None
        self._listeners: list = []
        
        # Repositories / services
        self.credit_repo: Optional[CreditRepository] = None
        self.credit_service: Optional[CreditService] = None
        
        # Tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
    
    async def startup(self) -> None:
        try:
            self.logger.info("Starting service components...")
            
            await self._init_messaging()
            await self._init_cache()
            await self._init_database()
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
                self.logger.error("Listener stop failed", exc_info=True)
        
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.error("Messaging client close failed", exc_info=True)
        
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception:
                self.logger.error("Redis close failed", exc_info=True)
        
        if self.prisma and self._db_connected:
            try:
                await self.prisma.disconnect()
            except Exception:
                self.logger.error("Prisma disconnect failed", exc_info=True)
        
        self.logger.info("%s shutdown complete", self.config.service_name)
    
    async def _init_messaging(self) -> None:
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])
        
        # Initialize publisher
        self.event_publisher = CreditEventPublisher(
            messaging=self.messaging_client,
            logger=self.logger
        )
        
        self.logger.info("Messaging client and publisher initialized")
    
    async def _init_cache(self) -> None:
        """Initialize Redis cache if enabled"""
        if not self.config.cache_enabled:
            self.logger.info("Cache disabled; skipping Redis initialization")
            return
        
        try:
            self.redis_client = await redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                max_connections=self.config.cache_max_connections
            )
            await self.redis_client.ping()
            self.logger.info("Redis cache initialized")
        except Exception as e:
            self.logger.warning(f"Redis initialization failed: {e}. Running without cache.")
            self.redis_client = None
    
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
    
    def _init_repositories(self) -> None:
        if self.config.db_enabled:
            if not (self.prisma and self._db_connected):
                raise RuntimeError("Prisma client not initialized/connected")
            
            self.credit_repo = CreditRepository(self.prisma)
            self.logger.info("Credit repository initialized")
        else:
            self.credit_repo = None
    
    def _init_local_services(self) -> None:
        if not self.credit_repo:
            raise RuntimeError("Credit repository not initialized")
        
        if not self.event_publisher:
            raise RuntimeError("Event publisher not initialized")
        
        self.credit_service = CreditService(
            config=self.config,
            repository=self.credit_repo,
            publisher=self.event_publisher,
            logger=self.logger,
            redis_client=self.redis_client
        )
        
        self.logger.info("Credit service initialized")
    
    async def _init_listeners(self) -> None:
        if not self.messaging_client or not self.credit_service:
            raise RuntimeError("Messaging or service layer not ready")
        
        # Credit grant listener
        grant_listener = BillingCreditGrantListener(
            js_client=self.messaging_client,
            service=self.credit_service,
            logger=self.logger
        )
        await grant_listener.start()
        self._listeners.append(grant_listener)
        
        # Trial activation listener
        trial_listener = BillingTrialActivatedListener(
            js_client=self.messaging_client,
            service=self.credit_service,
            logger=self.logger
        )
        await trial_listener.start()
        self._listeners.append(trial_listener)
        
        self.logger.info("Event listeners started")
    
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t
    
    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()
    
    def signal_shutdown(self) -> None:
        self._shutdown_event.set()

