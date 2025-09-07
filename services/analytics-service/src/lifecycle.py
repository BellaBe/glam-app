# services/analytics/src/lifecycle.py
from typing import Optional, List
import asyncio
from prisma import Prisma
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import ServiceConfig
from .repositories.analytics_repository import AnalyticsRepository
from .repositories.metrics_repository import MetricsRepository
from .repositories.aggregation_repository import AggregationRepository
from .services.analytics_service import AnalyticsService
from .services.aggregation_service import AggregationService
from .events.listeners import (
    SelfieAnalysisCompletedListener,
    RecommendationMatchCompletedListener,
    CreditsConsumedListener,
    CatalogSyncCompletedListener
)

from .jobs.aggregation_jobs import AggregationJobs

class ServiceLifecycle:
    """Manages all service components lifecycle"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Connections
        self.messaging_client: Optional[JetStreamClient] = None
        self.prisma: Optional[Prisma] = None
        self._db_connected = False
        
        # Scheduler for aggregation jobs
        self.scheduler: Optional[AsyncIOScheduler] = None
        
        # Components
        self.analytics_repo: Optional[AnalyticsRepository] = None
        self.metrics_repo: Optional[MetricsRepository] = None
        self.aggregation_repo: Optional[AggregationRepository] = None
        self.analytics_service: Optional[AnalyticsService] = None
        self.aggregation_service: Optional[AggregationService] = None
        
        # AggregationJobs
        self.aggregation_jobs: Optional[AggregationJobs] = None
        
        # Listeners
        self._listeners: List = []
        self._tasks: List[asyncio.Task] = []
    
    async def startup(self) -> None:
        """Initialize all components in correct order"""
        try:
            self.logger.info("Starting analytics service components...")
            
            # 1. Messaging (for events)
            await self._init_messaging()
            
            # 2. Database
            await self._init_database()
            
            # 3. Repositories
            self._init_repositories()
            
            # 4. Services
            self._init_services()
            
            # 5. Event listeners
            await self._init_listeners()
            
            # 6. Aggregation jobs
            if self.config.aggregation_enabled:
                await self._init_aggregation_jobs()
            
            self.logger.info(f"{self.config.service_name} started successfully")
            
        except Exception as e:
            self.logger.exception("Service startup failed", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Graceful shutdown in reverse order"""
        self.logger.info(f"Shutting down {self.config.service_name}")
        
        # Stop scheduler
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
        
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
        
        if self.aggregation_jobs:
            try:
                await self.aggregation_jobs.stop()
            except Exception:
                self.logger.exception("Aggregation jobs stop failed", exc_info=True)

        self.logger.info(f"{self.config.service_name} shutdown complete")
    
    async def _init_messaging(self) -> None:
        """Initialize NATS/JetStream for events"""
        self.messaging_client = JetStreamClient(self.logger)
        await self.messaging_client.connect([self.config.nats_url])
        await self.messaging_client.ensure_stream("GLAM_EVENTS", ["evt.*", "cmd.*"])
        self.logger.info("Messaging client initialized")
    
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
    
    def _init_repositories(self) -> None:
        """Initialize repositories with Prisma client"""
        if not self._db_connected:
            self.logger.warning("Database not connected, skipping repositories")
            return
        
        self.analytics_repo = AnalyticsRepository(self.prisma)
        self.metrics_repo = MetricsRepository(self.prisma)
        self.aggregation_repo = AggregationRepository(self.prisma)
        self.logger.info("Repositories initialized")
    
    def _init_services(self) -> None:
        """Initialize business services"""
        if not self.analytics_repo or not self.metrics_repo:
            raise RuntimeError("Repositories not initialized")
        
        self.analytics_service = AnalyticsService(
            analytics_repo=self.analytics_repo,
            metrics_repo=self.metrics_repo,
            logger=self.logger
        )
        
        self.aggregation_service = AggregationService(
            aggregation_repo=self.aggregation_repo,
            metrics_repo=self.metrics_repo,
            logger=self.logger
        )
        
        self.logger.info("Services initialized")
    
    async def _init_listeners(self) -> None:
        """Initialize event listeners"""
        if not self.messaging_client or not self.analytics_service:
            raise RuntimeError("Messaging or service not ready")
        
        # Create listeners
        listeners = [
            SelfieAnalysisCompletedListener(
                js_client=self.messaging_client,
                analytics_service=self.analytics_service,
                logger=self.logger
            ),
            RecommendationMatchCompletedListener(
                js_client=self.messaging_client,
                analytics_service=self.analytics_service,
                logger=self.logger
            ),
            CreditsConsumedListener(
                js_client=self.messaging_client,
                analytics_service=self.analytics_service,
                logger=self.logger
            ),
            CatalogSyncCompletedListener(
                js_client=self.messaging_client,
                analytics_service=self.analytics_service,
                logger=self.logger
            )
        ]
        
        # Start all listeners
        for listener in listeners:
            await listener.start()
            self._listeners.append(listener)
        
        self.logger.info(f"Started {len(listeners)} event listeners")
    
    async def _init_aggregation_jobs(self) -> None:
        """Initialize scheduled aggregation jobs"""
        if not self.aggregation_service:
            raise RuntimeError("Aggregation service not initialized")
        
        self.aggregation_jobs = AggregationJobs(
            config=self.config,
            aggregation_service=self.aggregation_service,
            logger=self.logger
        )
        
        await self.aggregation_jobs.start()
        self.logger.info("Aggregation jobs initialized")