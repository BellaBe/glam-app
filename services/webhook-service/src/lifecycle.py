# services/webhook-service/src/lifecycle.py
"""
Service lifecycle management for webhook service.

Manages initialization and cleanup of all service components.
"""

from __future__ import annotations

import asyncio
from typing import List, Optional, cast

from nats.js.api import StreamConfig, RetentionPolicy, StorageType
import redis.asyncio as redis

from shared.utils.logger import create_logger, ServiceLogger
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .config import ServiceConfig
from .services.auth_service import WebhookAuthService
from .services.deduplication_service import DeduplicationService
from .services.circuit_breaker_service import CircuitBreakerService
from .services.webhook_service import WebhookService

# repositories
from .repositories.webhook_repository import WebhookRepository
from .repositories.platform_config_repository import PlatformConfigRepository

# models
from .models.webhook_entry import WebhookEntry
from .models.platform_config import PlatformConfiguration

# events
from .events.publishers import WebhookEventPublisher


class ServiceLifecycle:
    """Manages lifecycle of webhook service components"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = create_logger(service_name=config.SERVICE_NAME)
        
        # Core infrastructure
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Repositories
        self.webhook_repo: Optional[WebhookRepository] = None
        self.platform_config_repo: Optional[PlatformConfigRepository] = None
        
        # Services
        self.auth_service: Optional[WebhookAuthService] = None
        self.dedup_service: Optional[DeduplicationService] = None
        self.circuit_breaker: Optional[CircuitBreakerService] = None
        self.webhook_service: Optional[WebhookService] = None
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
    
    async def startup(self):
        """Initialize all service components"""
        self.logger.info("Starting webhook service lifecycle")
        
        try:
            # 1. Database
            await self._init_database()
            
            # 2. Redis
            await self._init_redis()
            
            # 3. Messaging
            await self._init_messaging()
            
            # 4. Repositories
            self._init_repositories()
            
            # 5. Services
            self._init_services()
            
            # 6. Background tasks
            await self._start_background_tasks()
            
            self.logger.info("Webhook service lifecycle started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start webhook service: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Clean shutdown of all components"""
        self.logger.info("Shutting down webhook service lifecycle")
        
        # Cancel background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close connections
        if self.redis_client:
            await self.redis_client.close()
        
        if self.messaging_wrapper:
            await self.messaging_wrapper.close()
        
        if self.db_manager:
            await self.db_manager.close()
        
        self.logger.info("Webhook service lifecycle shutdown complete")
    
    async def _init_database(self):
        """Initialize database connection"""
        self.db_manager = DatabaseSessionManager(
            database_url=self.config.DATABASE_URL,
            echo=self.config.DB_ECHO
        )
        await self.db_manager.connect()
        
        # Create tables if needed
        from .models import Base
        async with self.db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Set global database manager
        set_database_manager(self.db_manager)
        
        self.logger.info("Database initialized")
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(
            self.config.REDIS_URL,
            decode_responses=True
        )
        await self.redis_client.ping()
        self.logger.info("Redis initialized")
    
    async def _init_messaging(self):
        """Initialize NATS/JetStream"""
        self.messaging_wrapper = JetStreamWrapper(logger=self.logger)
        await self.messaging_wrapper.connect([self.config.NATS_URL])
        
        # Ensure WEBHOOK stream exists
        stream_config = StreamConfig(
            name="WEBHOOK",
            subjects=[
                "evt.webhook.*",
                "evt.webhook.>",
                "cmd.webhook.*",
                "cmd.webhook.>"
            ],
            retention=RetentionPolicy.LIMITS,
            storage=StorageType.FILE,
            max_msgs=1_000_000,
            max_age=86400 * 7,  # 7 days
            max_msg_size=10 * 1024 * 1024,  # 10MB
            discard="old",
            num_replicas=3
        )
        
        js = self.messaging_wrapper._js
        try:
            await js.add_stream(stream_config)
            self.logger.info("Created WEBHOOK stream")
        except Exception:
            await js.update_stream(stream_config)
            self.logger.info("Updated WEBHOOK stream")
    
    def _init_repositories(self):
        """Initialize repositories"""
        if not self.db_manager:
            raise RuntimeError("Database not initialized")
        
        session_factory = self.db_manager.session_factory
        
        self.webhook_repo = WebhookRepository(session_factory)
        self.platform_config_repo = PlatformConfigRepository(session_factory)
        
        self.logger.info("Repositories initialized")
    
    def _init_services(self):
        """Initialize services"""
        if not all([
            self.webhook_repo,
            self.platform_config_repo,
            self.redis_client,
            self.messaging_wrapper
        ]):
            raise RuntimeError("Required dependencies not initialized")
        
        # Auth service
        self.auth_service = WebhookAuthService(
            platform_config_repo=self.platform_config_repo,
            shopify_secret=self.config.SHOPIFY_WEBHOOK_SECRET,
            stripe_secret=self.config.STRIPE_WEBHOOK_SECRET,
            logger=self.logger
        )
        
        # Deduplication service
        self.dedup_service = DeduplicationService(
            redis_client=self.redis_client,
            ttl_hours=self.config.DEDUP_TTL_HOURS,
            logger=self.logger
        )
        
        # Circuit breaker service
        self.circuit_breaker = CircuitBreakerService(
            redis_client=self.redis_client,
            failure_threshold=self.config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            timeout_seconds=self.config.CIRCUIT_BREAKER_TIMEOUT_SECONDS,
            window_seconds=self.config.CIRCUIT_BREAKER_WINDOW_SECONDS,
            logger=self.logger
        )
        
        # Publisher
        publisher = self.messaging_wrapper.create_publisher(WebhookEventPublisher)
        
        # Main webhook service
        self.webhook_service = WebhookService(
            webhook_repo=self.webhook_repo,
            auth_service=self.auth_service,
            dedup_service=self.dedup_service,
            circuit_breaker=self.circuit_breaker,
            publisher=publisher,
            logger=self.logger
        )
        
        self.logger.info("Services initialized")
    
    async def _start_background_tasks(self):
        """Start background tasks"""
        # Could add DLQ processor, metrics reporter, etc.
        pass