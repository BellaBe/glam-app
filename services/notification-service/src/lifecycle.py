# FIle: services/notification-service/src/lifecycle.py

import asyncio
from typing import Optional, List
from shared.utils.logger import create_logger
from shared.messaging.jetstream_wrapper import JetStreamWrapper
from shared.database import DatabaseSessionManager, set_database_manager
from .config import ServiceConfig
from .utils.template_engine import TemplateEngine
from .utils.rate_limiter import RateLimiter
from .services.email_service import EmailService
from nats.js.api import StreamConfig, RetentionPolicy, StorageType

class ServiceLifecycle:
    """Manages service lifecycle for notification service"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = create_logger(config.SERVICE_NAME)
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.email_service: Optional[EmailService] = None
        self.template_engine: Optional[TemplateEngine] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self._shutdown_event = asyncio.Event()
        self._tasks: List[asyncio.Task] = []
        
    async def _ensure_notification_stream(self):
        """Ensure the NOTIFICATION stream exists"""
        try:
            if not self.messaging_wrapper:
                raise RuntimeError("Messaging wrapper is not initialized")
            js = self.messaging_wrapper.js
            
            # Stream configuration
            stream_config = StreamConfig(
                name="NOTIFICATION",
                subjects=[
                    "cmd.notification.*",
                    "evt.notification.*"
                ],
                retention=RetentionPolicy.LIMITS,
                max_age=7 * 24 * 60 * 60,  # 7 days
                max_msgs=1000000,
                max_bytes=1024 * 1024 * 1024,  # 1GB
                storage=StorageType.FILE,
                num_replicas=1,
                duplicate_window=60,
            )
            
            try:
                # Check if stream exists
                info = await js.stream_info("NOTIFICATION")
                self.logger.info(f"Stream 'NOTIFICATION' already exists with {info.state.messages} messages")
            except:
                # Stream doesn't exist, create it
                info = await js.add_stream(stream_config)
                self.logger.info(f"Created stream 'NOTIFICATION' with subjects: {info.config.subjects}")
                
        except Exception as e:
            self.logger.error(f"Failed to ensure NOTIFICATION stream: {e}")
            raise
        
    async def startup(self):
        """Initialize all service dependencies"""
        try:
            # Initialize messaging
            self.messaging_wrapper = JetStreamWrapper(self.logger)
            await self.messaging_wrapper.connect(self.config.NATS_SERVERS)
            self.logger.info(f"{self.config.SERVICE_NAME} connected to NATS")
            
            # Ensure NOTIFICATION stream exists
            await self._ensure_notification_stream()
            
            self.logger.debug("CONFIG", self.config.model_dump())
            
            # Initialize database
            if self.config.DB_ENABLED and self.config.database_config:
                self.db_manager = DatabaseSessionManager(
                    database_url=self.config.database_config.database_url,
                    **self.config.database_config.get_engine_kwargs()
                )
                await self.db_manager.init()
                set_database_manager(self.db_manager)
                self.logger.info(f"{self.config.SERVICE_NAME} connected to database")
            
            # Initialize services
            self._init_services()
            
            # Import here to avoid circular imports
            from .events.subscribers import get_subscribers, set_notification_service
            from .events.publishers import get_publishers
            
            # Register publishers
            notification_publisher = None
            for publisher_class in get_publishers():
                publisher = self.messaging_wrapper.create_publisher(publisher_class)
                if publisher_class.__name__ == "NotificationPublisher":
                    notification_publisher = publisher
            
            if not notification_publisher:
                raise RuntimeError("NotificationPublisher not created")
            
            # Create notification service
            from .services.notification_service import NotificationService
            notification_service = NotificationService(
                publisher=notification_publisher,
                email_service=self.email_service,
                template_engine=self.template_engine,
                rate_limiter=self.rate_limiter,
                logger=self.logger
            )
            
            # Set the notification service for subscribers
            set_notification_service(notification_service)
            
            # Start subscribers
            for subscriber_class in get_subscribers():
                await self.messaging_wrapper.start_subscriber(subscriber_class)
            
            # Check email provider health
            health_status = await self.email_service.health_check()
            self.logger.info(f"Email provider health: {health_status}")
            
            self.logger.info(f"{self.config.SERVICE_NAME} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            await self.shutdown()
            raise
    
    def _init_services(self):
        """Initialize core services"""
        # Template engine
        self.template_engine = TemplateEngine()
        
        # Rate limiter
        self.rate_limiter = RateLimiter(self.config.rate_limit_config.model_dump())
        
        # Email service
        email_config = {
            'primary_provider': self.config.PRIMARY_PROVIDER,
            'fallback_provider': self.config.FALLBACK_PROVIDER,
            'sendgrid_config': self.config.sendgrid_config.model_dump(),
            'ses_config': self.config.ses_config.model_dump(),
            'smtp_config': self.config.smtp_config.model_dump(),
        }
        self.email_service = EmailService(email_config, self.logger)
    
    async def shutdown(self):
        """Cleanup all service resources"""
        self.logger.info(f"Shutting down {self.config.SERVICE_NAME}")
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Cleanup resources
        if self.messaging_wrapper:
            await self.messaging_wrapper.close()
            
        if self.db_manager:
            await self.db_manager.close()
        
        self.logger.info(f"{self.config.SERVICE_NAME} shutdown complete")
    
    def add_task(self, coro) -> asyncio.Task:
        """Add a background task to be managed"""
        task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self._shutdown_event.wait()
    
    def signal_shutdown(self):
        """Signal service to shutdown"""
        self._shutdown_event.set()