from typing import Optional, List
import asyncio
import redis.asyncio as redis
from prisma import Prisma
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from .config import ServiceConfig
from .repositories.billing_plan_repository import BillingPlanRepository
from .repositories.merchant_billing_repository import MerchantBillingRepository
from .repositories.merchant_trial_repository import MerchantTrialRepository
from .repositories.one_time_purchase_repository import OneTimePurchaseRepository
from .services.billing_service import BillingService
from .services.webhook_service import WebhookProcessingService
from .events.publishers import BillingEventPublisher
from .events.listeners import (
    AppSubscriptionUpdatedListener,
    AppPurchaseUpdatedListener,
    AppUninstalledListener
)

class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # External connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.prisma: Optional[Prisma] = None
        self.redis: Optional[redis.Redis] = None
        self._db_connected: bool = False
        
        # Publisher / listeners
        self.event_publisher: Optional[BillingEventPublisher] = None
        self._listeners: list = []
        
        # Repositories
        self.plan_repo: Optional[BillingPlanRepository] = None
        self.billing_repo: Optional[MerchantBillingRepository] = None
        self.trial_repo: Optional[MerchantTrialRepository] = None
        self.purchase_repo: Optional[OneTimePurchaseRepository] = None
        
        # Services
        self.billing_service: Optional[BillingService] = None
        self.webhook_service: Optional[WebhookProcessingService] = None
        
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
            self._init_services()
            await self._init_listeners()
            await self._init_scheduler()
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
        
        if self.messaging_client:
            try:
                await self.messaging_client.close()
            except Exception:
                self.logger.critical("Messaging client close failed")
        
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                self.logger.critical("Redis close failed")
        
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
        
        # Initialize publisher
        self.event_publisher = BillingEventPublisher(
            messaging=self.messaging_client,
            logger=self.logger,
        )
        self.logger.info("Messaging client and publisher initialized")
    
    async def _init_redis(self) -> None:
        """Initialize Redis client"""
        self.redis = await redis.from_url(
            self.config.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis.ping()
        self.logger.info("Redis connected")
    
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
            
            self.plan_repo = BillingPlanRepository(self.prisma)
            self.billing_repo = MerchantBillingRepository(self.prisma)
            self.trial_repo = MerchantTrialRepository(self.prisma)
            self.purchase_repo = OneTimePurchaseRepository(self.prisma)
            
            self.logger.info("Repositories initialized")
        else:
            raise RuntimeError("Database is required for billing service")
    
    def _init_services(self) -> None:
        if not all([self.plan_repo, self.billing_repo, self.trial_repo, self.purchase_repo, self.redis]):
            raise RuntimeError("Repositories not initialized")
        
        self.billing_service = BillingService(
            config=self.config,
            plan_repo=self.plan_repo,
            billing_repo=self.billing_repo,
            trial_repo=self.trial_repo,
            purchase_repo=self.purchase_repo,
            redis_client=self.redis,
            logger=self.logger,
        )
        
        self.webhook_service = WebhookProcessingService(
            config=self.config,
            billing_repo=self.billing_repo,
            purchase_repo=self.purchase_repo,
            billing_service=self.billing_service,
            redis_client=self.redis,
            logger=self.logger,
        )
        
        self.logger.info("Services initialized")
    
    async def _init_listeners(self) -> None:
        if not all([self.messaging_client, self.webhook_service, self.event_publisher]):
            raise RuntimeError("Required services not ready")
        
        # Subscription updated listener
        subscription_listener = AppSubscriptionUpdatedListener(
            js_client=self.messaging_client,
            webhook_service=self.webhook_service,
            publisher=self.event_publisher,
            logger=self.logger,
        )
        await subscription_listener.start()
        self._listeners.append(subscription_listener)
        
        # Purchase updated listener
        purchase_listener = AppPurchaseUpdatedListener(
            js_client=self.messaging_client,
            webhook_service=self.webhook_service,
            publisher=self.event_publisher,
            logger=self.logger,
        )
        await purchase_listener.start()
        self._listeners.append(purchase_listener)
        
        # App uninstalled listener
        uninstalled_listener = AppUninstalledListener(
            js_client=self.messaging_client,
            webhook_service=self.webhook_service,
            publisher=self.event_publisher,
            logger=self.logger,
        )
        await uninstalled_listener.start()
        self._listeners.append(uninstalled_listener)
        
        self.logger.info("Event listeners initialized")
    
    async def _init_scheduler(self) -> None:
        """Initialize trial expiry scheduler"""
        self.add_task(self._trial_expiry_loop())
        self.logger.info("Trial expiry scheduler started")
    
    async def _trial_expiry_loop(self) -> None:
        """Run trial expiry check every hour"""
        while not self._shutdown_event.is_set():
            try:
                # Run expiry check
                expired_domains = await self.billing_service.expire_trials()
                
                if expired_domains:
                    self.logger.info(
                        "Expired trials",
                        extra={"count": len(expired_domains), "domains": expired_domains}
                    )
                    
                    # Publish expired events
                    from ..schemas.billing import TrialExpiredPayload
                    for domain in expired_domains:
                        payload = TrialExpiredPayload(
                            shopDomain=domain,
                            expiredAt=datetime.utcnow()
                        )
                        await self.event_publisher.trial_expired(payload)
                
                # Wait for 1 hour or shutdown
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=3600  # 1 hour
                )
            except asyncio.TimeoutError:
                # Normal timeout, continue loop
                pass
            except Exception as e:
                self.logger.error("Trial expiry loop error", exc_info=True)
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t
    
    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()
    
    def signal_shutdown(self) -> None:
        self._shutdown_event.set()

