# services/catalog-ai-analyzer/src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.api import setup_middleware, create_health_router
from shared.utils import create_logger
from .config import get_service_config
from .lifecycle import ServiceLifecycle

# Create singletons
config = get_service_config()
logger = create_logger(config.service_name)
lifecycle = ServiceLifecycle(config, logger)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan management"""
    app.state.lifecycle = lifecycle
    app.state.config = config
    app.state.logger = logger  # REQUIRED for middleware
    
    try:
        await lifecycle.startup()
        yield
    finally:
        await lifecycle.shutdown()

def create_application() -> FastAPI:
    """Create FastAPI app"""
    app = FastAPI(
        title=config.service_name,
        version=config.service_version,
        description=config.service_description,
        lifespan=lifespan
    )
    
    # Setup shared middleware
    setup_middleware(app, service_name=config.service_name)
    
    # Add health check
    app.include_router(create_health_router(config.service_name))
    
    return app

app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug
    )