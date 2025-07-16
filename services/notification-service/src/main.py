# services/notification-service/src/main.py

"""Main entry point for the Notification Service"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from shared.api import setup_middleware
from shared.utils.logger import create_logger
from .config import get_service_config
from .lifecycle import ServiceLifecycle
from .api.v1 import health, notifications, templates

# Global singletons
config = get_service_config()
logger = create_logger(config.service_name)
lifecycle = ServiceLifecycle(config, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan adapter"""
   
    logger.info(f"Starting {config.service_name}", extra={
        "service_name": config.service_name,
        "version": config.service_version,
        "environment": config.environment,
        "api_host": config.api_host,
        "api_port": config.effective_port,
    })
    app.state.lifecycle = lifecycle
    app.state.config = config
    app.state.logger = logger
    try:
        await lifecycle.startup()
        yield
    finally:
        await lifecycle.shutdown()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=config.service_name,
        version=config.service_version,
        lifespan=lifespan,
        description="Email notification service for GlamYouUp platform",
        exception_handlers={} # Use shared middleware for exception handling
    )
    
    setup_middleware(
        app,
        service_name=config.service_name,
        enable_metrics=True
    )
    
    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
    app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    
    port = config.effective_port
    uvicorn.run(
        "src.main:app",
        host=config.api_host,
        port=port,
        reload=config.debug
    )
