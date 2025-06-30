# services/notification-service/src/main.py
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database.async_db import create_async_db_engine
from src.database.init_db import init_db
from src.events.subscribers import EventSubscriber
from src.events.publishers import EventPublisher
from src.routes.notifications import notifications_router
from src.routes.preferences import preferences_router
from src.routes.templates import templates_router
from src.routes.health import health_router
from src.services.email_service import EmailService
from src.services.notification_service import NotificationService
from src.repositories.notification_repository import NotificationRepository
from src.repositories.preferences_repository import PreferencesRepository
from src.repositories.template_repository import TemplateRepository
from src.utils.nats_wrapper import NatsWrapper
from src.utils.redis_wrapper import RedisWrapper
from src.utils.logger import logger, setup_logging

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    setup_logging(settings.log_level)
    logger.info(f"🚀 Starting Notification Service, external port {settings.external_port}")
    
    # Initialize database
    logger.info(f"📊 Creating database engine with DATABASE_URL={settings.database_url}")
    engine, AsyncSessionLocal = await create_async_db_engine(settings.database_url)
    app.state.db_engine = engine
    app.state.db_session = AsyncSessionLocal
    await init_db(engine)
    
    # Initialize NATS
    nats_wrapper = NatsWrapper()
    await nats_wrapper.connect([settings.nats_url])
    app.state.nats = nats_wrapper
    logger.info(f"📡 Connected to NATS at {settings.nats_url}")
    
    # Initialize Redis
    redis_wrapper = RedisWrapper()
    await redis_wrapper.connect(settings.redis_url)
    app.state.redis = redis_wrapper
    logger.info(f"💾 Connected to Redis at {settings.redis_url}")
    
    # Initialize repositories
    notification_repo = NotificationRepository(AsyncSessionLocal)
    preferences_repo = PreferencesRepository(AsyncSessionLocal)
    template_repo = TemplateRepository(AsyncSessionLocal)
    
    # Initialize services
    email_service = EmailService(settings)
    publisher = EventPublisher(nats_wrapper.client)
    
    notification_service = NotificationService(
        email_service=email_service,
        notification_repo=notification_repo,
        preferences_repo=preferences_repo,
        template_repo=template_repo,
        publisher=publisher,
        redis=redis_wrapper,
    )
    
    # Attach services to app state for route access
    app.state.notification_service = notification_service
    app.state.notification_repo = notification_repo
    app.state.preferences_repo = preferences_repo
    app.state.template_repo = template_repo
    
    # Initialize and start event subscriber
    subscriber = EventSubscriber(
        nats_wrapper=nats_wrapper,
        notification_service=notification_service,
    )
    
    # Start subscriptions in background
    subscription_task = asyncio.create_task(subscriber.start())
    app.state.subscription_task = subscription_task
    
    logger.info("✅ Notification Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down Notification Service...")
    
    # Cancel subscription task
    subscription_task.cancel()
    try:
        await subscription_task
    except asyncio.CancelledError:
        pass
    
    # Close connections
    await nats_wrapper.close()
    await redis_wrapper.close()
    await engine.dispose()
    
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