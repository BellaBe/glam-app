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
logger = create_logger(config.service_name)
lifecycle = ServiceLifecycle(config, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    
    logger.info(
        f"Starting {config.service_name}",
        extra={
            "version": config.service_version,
            "environment": config.environment,
            "api_host": config.api_host,
            "api_port": config.effective_port,
        }
    )
    
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
        title=config.service_name,
        version=config.service_version,
        lifespan=lifespan,
        description="Credit management service for merchant credits and plugin access control",
        exception_handlers={}  # Use shared middleware for exception handling
    )

    setup_middleware(
        app,
        service_name=config.service_name,
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
    
    # Smart port selection
    port = config.effective_port
    
    logger.info(f"Starting server", extra={
        "internal_port": config.api_port,
        "external_port": config.api_external_port,
        "effective_port": port,
        "environment": config.environment
    })
    
    uvicorn.run(
        "src.main:app",
        host=config.api_host,
        port=port,
        reload=config.debug
    )