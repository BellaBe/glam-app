from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.api import setup_middleware
from shared.api.health import create_health_router
from shared.utils.logger import create_logger
from .config import get_service_config
from .lifecycle import ServiceLifecycle
from .api.router import router

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
        "api_port": config.effective_api_port,
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
        description="Merchant service for GlamYouUp platform - manages merchant identity and consent",
    )
    
    setup_middleware(
        app,
        service_name=config.service_name,
        enable_metrics=config.monitoring_metrics_enabled,
        metrics_path="/metrics"
    )
    
    # Include routers
    app.include_router(create_health_router(config.service_name))
    app.include_router(router)
    
    return app

app = create_application()

if __name__ == "__main__":
    import uvicorn
    port = config.effective_api_port
    uvicorn.run(
        "src.main:app",
        host=config.api_host,
        port=port,
        reload=config.debug
    )

