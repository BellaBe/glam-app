from contextlib import asynccontextmanager
from typing import Optional, List
import asyncio
import redis.asyncio as redis
from shared.database import DatabaseSessionManager, set_database_manager
from shared.messaging import JetStreamWrapper
from shared.utils.logger import create_logger
from .config import AnalyticsConfig
from .repositories.analytics_repository import (
    AnalyticsRepository, OrderAnalyticsRepository, LifecycleTrialAnalyticsRepository,
    UsagePatternRepository, PredictionModelRepository, EngagementMetricRepository,
    ShopifyAnalyticsRepository
)
from .repositories.alert_repository import AlertRuleRepository, AlertHistoryRepository
from .repositories.platform_repository import PlatformMetricsRepository
from .mappers.analytics_mapper import (
    UsageAnalyticsMapper, OrderAnalyticsMapper, LifecycleTrialAnalyticsMapper,
    UsagePatternMapper, PredictionModelMapper, EngagementMetricMapper,
    ShopifyAnalyticsMapper, AlertRuleMapper, AlertHistoryMapper, PlatformMetricsMapper
)
from .services.analytics_service import AnalyticsService
from .services.alert_service import AlertService
from .services.pattern_detection_service import PatternDetectionService
from .services.prediction_service import PredictionService
from .events.publishers import AnalyticsEventPublisher
from .events.subscribers import (
    CreditEventSubscriber, AIEventSubscriber, MerchantEventSubscriber,
    ShopifyEventSubscriber, AuthEventSubscriber
)

class AnalyticsLifecycle:
    """Manages analytics service lifecycle and dependencies"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = create_logger(config.service_name)
        
        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Repositories
        self.usage_repo: Optional[AnalyticsRepository] = None
        self.order_repo: Optional[OrderAnalyticsRepository] = None
        self.trial_repo: Optional[LifecycleTrialAnalyticsRepository] = None
        self.pattern_repo: Optional[UsagePatternRepository] = None
        self.prediction_repo: Optional[PredictionModelRepository] = None
        self.engagement_repo: Optional[EngagementMetricRepository] = None
        self.shopify_repo: Optional[ShopifyAnalyticsRepository] = None
        self.alert_rule_repo: Optional[AlertRuleRepository] = None
        self.alert_history_repo: Optional[AlertHistoryRepository] = None
        self.platform_repo: Optional[PlatformMetricsRepository] = None
        
        # Mappers
        self.usage_mapper: Optional[UsageAnalyticsMapper] = None
        self.order_mapper: Optional[OrderAnalyticsMapper] = None
        self.trial_mapper: Optional[LifecycleTrialAnalyticsMapper] = None
        self.pattern_mapper: Optional[UsagePatternMapper] = None
        self.prediction_mapper: Optional[PredictionModelMapper] = None
        self.engagement_mapper: Optional[EngagementMetricMapper] = None
        self.shopify_mapper: Optional[ShopifyAnalyticsMapper] = None
        self.alert_rule_mapper: Optional[AlertRuleMapper] = None
        self.alert_history_mapper: Optional[AlertHistoryMapper] = None
        self.platform_mapper: Optional[PlatformMetricsMapper] = None
        
        # Services
        self.analytics_service: Optional[AnalyticsService] = None
        self.alert_service: Optional[AlertService] = None
        self.pattern_service: Optional[PatternDetectionService] = None
        self.prediction_service: Optional[PredictionService] = None
        
        # Event handling
        self.event_publisher: Optional[AnalyticsEventPublisher] = None
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
    
    async def startup(self) -> None:
        """Initialize all components in dependency order"""
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
        self.event_publisher = self.messaging_wrapper.create_publisher(AnalyticsEventPublisher)
        
        # 5. Initialize repositories
        if self.db_manager:
            session_factory = self.db_manager.session_factory
            self.usage_repo = AnalyticsRepository(session_factory)
            self.order_repo = OrderAnalyticsRepository(session_factory)
            self.trial_repo = LifecycleTrialAnalyticsRepository(session_factory)
            self.pattern_repo = UsagePatternRepository(session_factory)
            self.prediction_repo = PredictionModelRepository(session_factory)
            self.engagement_repo = EngagementMetricRepository(session_factory)
            self.shopify_repo = ShopifyAnalyticsRepository(session_factory)
            self.alert_rule_repo = AlertRuleRepository(session_factory)
            self.alert_history_repo = AlertHistoryRepository(session_factory)
            self.platform_repo = PlatformMetricsRepository(session_factory)
        
        # 6. Initialize mappers
        self.usage_mapper = UsageAnalyticsMapper()
        self.order_mapper = OrderAnalyticsMapper()
        self.trial_mapper = LifecycleTrialAnalyticsMapper()
        self.pattern_mapper = UsagePatternMapper()
        self.prediction_mapper = PredictionModelMapper()
        self.engagement_mapper = EngagementMetricMapper()
        self.shopify_mapper = ShopifyAnalyticsMapper()
        self.alert_rule_mapper = AlertRuleMapper()
        self.alert_history_mapper = AlertHistoryMapper()
        self.platform_mapper = PlatformMetricsMapper()
        
        # 7. Initialize services
        self.pattern_service = PatternDetectionService(
            usage_repo=self.usage_repo,
            pattern_repo=self.pattern_repo,
            logger=self.logger,
            config=self.config
        )
        
        self.prediction_service = PredictionService(
            usage_repo=self.usage_repo,
            order_repo=self.order_repo,
            trial_repo=self.trial_repo,
            prediction_repo=self.prediction_repo,
            prediction_mapper=self.prediction_mapper,
            logger=self.logger,
            config=self.config
        )
        
        self.analytics_service = AnalyticsService(
            usage_repo=self.usage_repo,
            order_repo=self.order_repo,
            trial_repo=self.trial_repo,
            pattern_repo=self.pattern_repo,
            prediction_repo=self.prediction_repo,
            engagement_repo=self.engagement_repo,
            shopify_repo=self.shopify_repo,
            usage_mapper=self.usage_mapper,
            order_mapper=self.order_mapper,
            trial_mapper=self.trial_mapper,
            pattern_mapper=self.pattern_mapper,
            prediction_mapper=self.prediction_mapper,
            engagement_mapper=self.engagement_mapper,
            shopify_mapper=self.shopify_mapper,
            publisher=self.event_publisher,
            pattern_service=self.pattern_service,
            prediction_service=self.prediction_service,
            logger=self.logger,
            config=self.config
        )
        
        self.alert_service = AlertService(
            rule_repo=self.alert_rule_repo,
            history_repo=self.alert_history_repo,
            rule_mapper=self.alert_rule_mapper,
            history_mapper=self.alert_history_mapper,
            publisher=self.event_publisher,
            logger=self.logger,
            config=self.config
        )
        
        # 8. Register dependencies for subscribers
        self.messaging_wrapper.register_dependency("analytics_service", self.analytics_service)
        self.messaging_wrapper.register_dependency("alert_service", self.alert_service)
        self.messaging_wrapper.register_dependency("logger", self.logger)
        
        # 9. Start event subscribers
        await self.messaging_wrapper.start_subscriber(CreditEventSubscriber)
        await self.messaging_wrapper.start_subscriber(AIEventSubscriber)
        await self.messaging_wrapper.start_subscriber(MerchantEventSubscriber)
        await self.messaging_wrapper.start_subscriber(ShopifyEventSubscriber)
        await self.messaging_wrapper.start_subscriber(AuthEventSubscriber)
        
        # 10. Start background tasks
        if not self.config.debug:  # Only in production
            self._start_background_tasks()
        
        self.logger.info("Analytics service startup complete")
    
    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        self.logger.info(f"Shutting down {self.config.service_name}")
        
        # Cancel background tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close connections
        if self.messaging_wrapper:
            await self.messaging_wrapper.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        if self.db_manager:
            await self.db_manager.close()
        
        self.logger.info("Analytics service shutdown complete")
    
    def _start_background_tasks(self) -> None:
        """Start background processing tasks"""
        # Daily analytics aggregation task
        daily_task = asyncio.create_task(self._daily_analytics_task())
        self._tasks.append(daily_task)
        
        # Real-time alert evaluation task
        alert_task = asyncio.create_task(self._alert_evaluation_task())
        self._tasks.append(alert_task)
        
        # Pattern detection task
        pattern_task = asyncio.create_task(self._pattern_detection_task())
        self._tasks.append(pattern_task)
        
        self.logger.info("Started background tasks")
    
    async def _daily_analytics_task(self) -> None:
        """Daily analytics aggregation task"""
        while True:
            try:
                # Wait until 02:30 UTC (configured time)
                await asyncio.sleep(60)  # Check every minute
                
                now = asyncio.get_event_loop().time()
                # Simplified scheduling - in production, use proper cron scheduling
                
                # Process daily aggregations
                # This would trigger daily batch processing
                self.logger.info("Running daily analytics aggregation")
                
                # Sleep for 23 hours before next run
                await asyncio.sleep(23 * 60 * 60)
                
            except Exception as e:
                self.logger.error(f"Daily analytics task error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _alert_evaluation_task(self) -> None:
        """Real-time alert evaluation task"""
        while True:
            try:
                # Process alerts every 30 seconds (configurable)
                await asyncio.sleep(self.config.processing_interval_seconds)
                
                # This would evaluate alert rules against current metrics
                # For demo purposes, just log
                self.logger.debug("Evaluating alert rules")
                
            except Exception as e:
                self.logger.error(f"Alert evaluation task error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _pattern_detection_task(self) -> None:
        """Background pattern detection task"""
        while True:
            try:
                # Run pattern detection every hour
                await asyncio.sleep(3600)
                
                self.logger.info("Running background pattern detection")
                
                # This would process pattern detection for active merchants
                # Implementation would batch process merchants
                
            except Exception as e:
                self.logger.error(f"Pattern detection task error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry


