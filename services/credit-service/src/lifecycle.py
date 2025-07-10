"""
Service lifecycle management for credit service.

Manages startup and shutdown of all service components following
the same pattern as notification service.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import redis.asyncio as redis
from nats.js.api import StreamConfig, RetentionPolicy, StorageType

from shared.utils.logger import ServiceLogger
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .config import ServiceConfig
from .services.credit_service import CreditService
from .services.balance_monitor_service import BalanceMonitorService
from .services.plugin_status_service import PluginStatusService

# Repositories
from .repositories.credit_account_repository import CreditAccountRepository
from .repositories.credit_transaction_repository import CreditTransactionRepository

# Models
from .models.credit_account import CreditAccount
from .models.credit_transaction import CreditTransaction

# Events
from .events.publishers import CreditEventPublisher
from .events.subscribers import (
    ShopifyOrderPaidSubscriber,
    ShopifyOrderRefundedSubscriber,
    BillingPaymentSucceededSubscriber,
    MerchantCreatedSubscriber,
    ManualAdjustmentSubscriber
)

# Mappers
from .mappers.credit_account_mapper import CreditAccountMapper
from .mappers.credit_transaction_mapper import CreditTransactionMapper


class ServiceLifecycle:
    """Manages service lifecycle and dependencies"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Core infrastructure
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.redis_client: Optional[redis.Redis] = None
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        
        # Repositories
        self.credit_account_repo: Optional[CreditAccountRepository] = None
        self.credit_transaction_repo: Optional[CreditTransactionRepository] = None
        
        # Mappers
        self.credit_account_mapper: Optional[CreditAccountMapper] = None
        self.credit_transaction_mapper: Optional[CreditTransactionMapper] = None
        
        # Services
        self.credit_service: Optional[CreditService] = None
        self.balance_monitor_service: Optional[BalanceMonitorService] = None
        self.plugin_status_service: Optional[PluginStatusService] = None
        
        # Events
        self.credit_publisher: Optional[CreditEventPublisher] = None
        
        # Subscribers
        self.subscribers: list = []
        
        # Background tasks
        self._background_tasks: set[asyncio.Task] = set()
    
    async def startup(self) -> None:
        """Start all service components"""
        
        try:
            self.logger.info("Starting service components...")
            
            # 1. Initialize database
            await self._setup_database()
            
            # 2. Initialize Redis
            await self._setup_redis()
            
            # 3. Initialize messaging
            await self._setup_messaging()
            
            # 4. Initialize repositories
            self._setup_repositories()
            
            # 5. Initialize mappers
            self._setup_mappers()
            
            # 6. Initialize services
            self._setup_services()
            
            # 7. Initialize events
            await self._setup_events()
            
            # 8. Start subscribers
            await self._start_subscribers()
            
            self.logger.info("All service components started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Shutdown all service components"""
        
        self.logger.info("Shutting down service components...")
        
        # Stop background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
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
    
    async def _setup_database(self) -> None:
        """Initialize database connection and create tables"""
        
        self.logger.info("Setting up database...")
        
        self.db_manager = DatabaseSessionManager(
            database_url=self.config.DATABASE_URL,
            pool_size=self.config.DATABASE_POOL_SIZE,
            max_overflow=self.config.DATABASE_MAX_OVERFLOW
        )
        
        # Set global database manager
        set_database_manager(self.db_manager)
        
        # Create tables
        async with self.db_manager.get_engine().begin() as conn:
            from .models.base import Base
            await conn.run_sync(Base.metadata.create_all)
        
        self.logger.info("Database setup complete")
    
    async def _setup_redis(self) -> None:
        """Initialize Redis connection"""
        
        self.logger.info("Setting up Redis...")
        
        self.redis_client = redis.from_url(
            self.config.REDIS_URL,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        await self.redis_client.ping()
        
        self.logger.info("Redis setup complete")
    
    async def _setup_messaging(self) -> None:
        """Initialize NATS JetStream messaging"""
        
        self.logger.info("Setting up messaging...")
        
        self.messaging_wrapper = JetStreamWrapper(
            nats_url=self.config.NATS_URL,
            logger=self.logger
        )
        
        await self.messaging_wrapper.connect()
        
        # Ensure CREDIT stream exists
        credit_stream_config = StreamConfig(
            name="CREDIT",
            subjects=["evt.credits.*", "cmd.credits.*"],
            retention=RetentionPolicy.LIMITS,
            storage=StorageType.FILE,
            max_age=30 * 24 * 60 * 60,  # 30 days
            max_msgs=1000000
        )
        
        await self.messaging_wrapper.ensure_stream(credit_stream_config)
        
        self.logger.info("Messaging setup complete")
    
    def _setup_repositories(self) -> None:
        """Initialize repositories"""
        
        self.logger.info("Setting up repositories...")
        
        session_factory = self.db_manager.get_session_factory()
        
        self.credit_account_repo = CreditAccountRepository(session_factory)
        self.credit_transaction_repo = CreditTransactionRepository(session_factory)
        
        self.logger.info("Repositories setup complete")
    
    def _setup_mappers(self) -> None:
        """Initialize mappers"""
        
        self.logger.info("Setting up mappers...")
        
        self.credit_account_mapper = CreditAccountMapper()
        self.credit_transaction_mapper = CreditTransactionMapper()
        
        self.logger.info("Mappers setup complete")
    
    def _setup_services(self) -> None:
        """Initialize business services"""
        
        self.logger.info("Setting up services...")
        
        # Create publisher first (will be properly initialized in events setup)
        self.credit_publisher = CreditEventPublisher(
            jetstream_wrapper=self.messaging_wrapper,
            logger=self.logger
        )
        
        # Balance monitor service
        self.balance_monitor_service = BalanceMonitorService(
            config=self.config,
            publisher=self.credit_publisher,
            logger=self.logger
        )
        
        # Plugin status service
        self.plugin_status_service = PluginStatusService(
            config=self.config,
            account_repo=self.credit_account_repo,
            redis_client=self.redis_client,
            logger=self.logger
        )
        
        # Main credit service
        self.credit_service = CreditService(
            config=self.config,
            publisher=self.credit_publisher,
            account_repo=self.credit_account_repo,
            transaction_repo=self.credit_transaction_repo,
            balance_monitor=self.balance_monitor_service,
            account_mapper=self.credit_account_mapper,
            transaction_mapper=self.credit_transaction_mapper,
            logger=self.logger
        )
        
        self.logger.info("Services setup complete")
    
    async def _setup_events(self) -> None:
        """Initialize event publishers"""
        
        self.logger.info("Setting up events...")
        
        # Register publisher with messaging wrapper
        await self.messaging_wrapper.register_publisher(
            CreditEventPublisher,
            jetstream_wrapper=self.messaging_wrapper,
            logger=self.logger
        )
        
        self.logger.info("Events setup complete")
    
    async def _start_subscribers(self) -> None:
        """Start event subscribers"""
        
        self.logger.info("Starting event subscribers...")
        
        # Create subscribers
        subscribers = [
            ShopifyOrderPaidSubscriber(
                jetstream_wrapper=self.messaging_wrapper,
                credit_service=self.credit_service,
                logger=self.logger
            ),
            ShopifyOrderRefundedSubscriber(
                jetstream_wrapper=self.messaging_wrapper,
                credit_service=self.credit_service,
                logger=self.logger
            ),
            BillingPaymentSucceededSubscriber(
                jetstream_wrapper=self.messaging_wrapper,
                credit_service=self.credit_service,
                logger=self.logger
            ),
            MerchantCreatedSubscriber(
                jetstream_wrapper=self.messaging_wrapper,
                credit_service=self.credit_service,
                logger=self.logger
            ),
            ManualAdjustmentSubscriber(
                jetstream_wrapper=self.messaging_wrapper,
                credit_service=self.credit_service,
                logger=self.logger
            )
        ]
        
        # Start subscriber tasks
        for subscriber in subscribers:
            # Subscribe to specific events based on subscriber type
            if isinstance(subscriber, ShopifyOrderPaidSubscriber):
                task = asyncio.create_task(
                    subscriber.subscribe_to_event("evt.shopify.webhook.order_paid", subscriber.handle_order_paid)
                )
            elif isinstance(subscriber, ShopifyOrderRefundedSubscriber):
                task = asyncio.create_task(
                    subscriber.subscribe_to_event("evt.shopify.webhook.order_refunded", subscriber.handle_order_refunded)
                )
            elif isinstance(subscriber, BillingPaymentSucceededSubscriber):
                task = asyncio.create_task(
                    subscriber.subscribe_to_event("evt.billing.payment_succeeded", subscriber.handle_payment_succeeded)
                )
            elif isinstance(subscriber, MerchantCreatedSubscriber):
                task = asyncio.create_task(
                    subscriber.subscribe_to_event("evt.merchant.created", subscriber.handle_merchant_created)
                )
            elif isinstance(subscriber, ManualAdjustmentSubscriber):
                task = asyncio.create_task(
                    subscriber.subscribe_to_event("evt.credits.manual_adjustment", subscriber.handle_manual_adjustment)
                )
            
            self._background_tasks.add(task)
            self.subscribers.append(subscriber)
            
            # Clean up completed tasks
            task.add_done_callback(self._background_tasks.discard)
        
        self.logger.info(f"Started {len(subscribers)} event subscribers")
```