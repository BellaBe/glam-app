# services/notification-service/src/main.py

"""Main entry point for the Notification Service"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from shared.api import setup_middleware
from .config import get_service_config
from .lifecycle import ServiceLifecycle
from .routers import health, notifications, templates

# Global singletons
config = get_service_config()
lifecycle = ServiceLifecycle(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan adapter"""
    # Store lifecycle in app state for access in dependencies
    app.state.lifecycle = lifecycle
    app.state.config = config
    
    await lifecycle.startup()
    try:
        yield
    finally:
        await lifecycle.shutdown()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=config.SERVICE_NAME,
        version=config.SERVICE_VERSION,
        lifespan=lifespan,
        description="Email notification service for GlamYouUp platform",
        # Disable default exception handlers as shared middleware handles them
        exception_handlers={}
    )
    
    # Set up all standard middleware (metrics + API)
    setup_middleware(
        app,
        service_name=config.SERVICE_NAME,
        enable_metrics=True,  # Enable Prometheus metrics
    )
    
    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(
        notifications.router,
        prefix="/api/v1/notifications",
        tags=["notifications"]
    )
    app.include_router(
        templates.router,
        prefix="/api/v1/templates",
        tags=["templates"]
    )

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "services.notification_service.src.main:app",
        host="0.0.0.0",
        port=config.API_PORT,
        reload=config.DEBUG
    )
