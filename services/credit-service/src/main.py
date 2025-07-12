# services/credit-service/src/main.py
"""Credit Service main application."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from shared.utils.logger import create_logger
from shared.api import setup_middleware
from .config import get_service_config
from .lifecycle import ServiceLifecycle
from .api.v1 import health, credits, transactions, plugin_status

# Global singletons
config = get_service_config()
logger = create_logger(config.SERVICE_NAME)
lifecycle = ServiceLifecycle(config, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    
    logger.info("Starting Credit Service", version=config.SERVICE_VERSION)
    
    app.state.lifecycle = lifecycle
    app.state.config = config
    app.state.logger = logger
    
    try:
        await lifecycle.startup()
        logger.info("Credit Service started successfully")
        yield
    finally:
        logger.info("Shutting down Credit Service")
        await lifecycle.shutdown()
        logger.info("Credit Service stopped")
        
def create_application() -> FastAPI:

    # Create FastAPI app
    app = FastAPI(
        title=config.SERVICE_NAME,
        version=config.SERVICE_VERSION,
        lifespan=lifespan,
        description="Credit management service for merchant credits and plugin access control",
        exception_handlers={}  # Use shared middleware for exception handling
    )

    setup_middleware(
        app,
        service_name=config.SERVICE_NAME,
        enable_metrics=True
    )

    # Include routers
    app.include_router(health.router, prefix="/api/v1/credits")
    app.include_router(credits.router, prefix="/api/v1/credits")
    app.include_router(transactions.router, prefix="/api/v1/credits")
    app.include_router(plugin_status.router, prefix="/api/v1")
    
    return app

app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=config.SERVICE_PORT,
        reload=config.DEBUG
    )