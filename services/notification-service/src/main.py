# services/notification-service/src/main.py
import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.database.config import DatabaseConfig
from shared.database.session import DatabaseSessionManager
from shared.database.dependencies import set_database_manager
from shared.database.migrations import MigrationManager
from shared.messaging.jetstream_wrapper import JetStreamWrapper
from shared.utils.logger import create_logger

from src.config import settings
from src.events.publishers import CatalogPublisher, NotificationPublisher
from src.events.subscribers import (
    SendEmailCommandSubscriber,
    SendBulkEmailCommandSubscriber,
    ScheduleEmailCommandSubscriber,
    CancelScheduledCommandSubscriber,
    UpdatePreferencesCommandSubscriber,
    ShopLaunchedSubscriber,
    CatalogRegistrationCompletedSubscriber,
    CatalogSyncCompletedSubscriber,
    BillingSubscriptionUpdatedSubscriber,
    BillingPurchaseCompletedSubscriber,
    BillingBalanceLowSubscriber,
    BillingBalanceZeroSubscriber,
    BillingFeaturesDeactivatedSubscriber,
)
from src.routes.notifications import notifications_router
from src.routes.preferences import preferences_router
from src.routes.templates import templates_router
from src.routes.health import health_router
from src.services.email_service import EmailService
from src.services.notification_service import NotificationService
from src.repositories.notification_repository import NotificationRepository
from src.repositories.preferences_repository import PreferencesRepository
from src.repositories.template_repository import TemplateRepository
from src.repositories.scheduled_repository import ScheduledNotificationRepository
from src.repositories.frequency_limit_repository import FrequencyLimitRepository
from src.utils.redis_wrapper import RedisWrapper

load_dotenv()

# Initialize logger
logger = create_logger("notification-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"🚀 Starting Notification Service, external port {settings.external_port}")
    
    # Initialize database
    db_config = DatabaseConfig()
    db_manager = DatabaseSessionManager(
        database_url=db_config.database_url,
        **db_config.get_engine_kwargs()
    )
    await db_manager.init()
    set_database_manager(db_manager)
    app.state.db_manager = db_manager
    
    # Run migrations
    migration_manager = MigrationManager(
        service_name=settings.service_name,
        alembic_ini_path="alembic.ini",
        migrations_path="src/migrations",
        database_url=db_config.sync_database_url
    )
    migration_manager.upgrade()
    
    # Initialize JetStream
    jetstream_wrapper = JetStreamWrapper(logger)
    await jetstream_wrapper.connect([settings.nats_url])
    app.state.jetstream = jetstream_wrapper
    
    # Initialize Redis
    redis_wrapper = RedisWrapper()
    await redis_wrapper.connect(settings.redis_url)
    app.state.redis = redis_wrapper
    
    # Initialize repositories
    notification_repo = NotificationRepository()
    preferences_repo = PreferencesRepository()
    template_repo = TemplateRepository()
    frequency_limit_repo = FrequencyLimitRepository()
    
    # Initialize publishers
    notification_publisher = await jetstream_wrapper.create_publisher(NotificationPublisher)
    catalog_publisher = await jetstream_wrapper.create_publisher(CatalogPublisher)
    
    # Initialize services
    email_service = EmailService(settings)
    notification_service = NotificationService(
        email_service=email_service,
        notification_repo=notification_repo,
        preferences_repo=preferences_repo,
        template_repo=template_repo,
        frequency_limit_repo=frequency_limit_repo,
        publisher=notification_publisher,
        redis=redis_wrapper,
        logger=logger,
    )
    
    # Attach services to app state
    app.state.notification_service = notification_service
    app.state.notification_repo = notification_repo
    app.state.preferences_repo = preferences_repo
    app.state.template_repo = template_repo
    
    # Initialize and start subscribers
    subscribers = [
        SendEmailCommandSubscriber(notification_service),
        SendBulkEmailCommandSubscriber(notification_service),
        UpdatePreferencesCommandSubscriber(notification_service),
        ShopLaunchedSubscriber(notification_service),
        CatalogRegistrationCompletedSubscriber(notification_service),
        CatalogSyncCompletedSubscriber(notification_service),
        BillingSubscriptionUpdatedSubscriber(notification_service),
        BillingPurchaseCompletedSubscriber(notification_service),
        BillingBalanceLowSubscriber(notification_service),
        BillingBalanceZeroSubscriber(notification_service),
        BillingFeaturesDeactivatedSubscriber(notification_service),
    ]
    
    # Start all subscribers
    for subscriber in subscribers:
        await jetstream_wrapper.start_subscriber(subscriber)
    
    logger.info("✅ Notification Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down Notification Service...")
    await jetstream_wrapper.close()
    await redis_wrapper.close()
    await db_manager.close()
    logger.info("✅ Notification Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Email notification service for GlamYouUp platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(preferences_router, prefix="/api/v1/preferences", tags=["Preferences"])
app.include_router(templates_router, prefix="/api/v1/templates", tags=["Templates"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "dev",
    )