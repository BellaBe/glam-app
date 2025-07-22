# services/merchant-service/src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.api import setup_middleware
from shared.api.health import create_health_router
from shared.utils.logger import create_logger
from .config import get_service_config
from .lifecycle import ServiceLifecycle
from .api.v1 import router as merchants_router

# Create lifecycle manager
config = get_service_config()
logger = create_logger(config.service_name)
lifecycle = ServiceLifecycle(config, logger)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    await lifecycle.startup()
    
    # Store dependencies in app state
    app.state.lifecycle = lifecycle
    app.state.config = config
    
    yield
    
    # Shutdown
    await lifecycle.shutdown()

# Create FastAPI app
app = FastAPI(
    title=config.service_name,
    version=config.service_version,
    lifespan=lifespan
)

# Setup middleware from shared package
setup_middleware(
    app,
    service_name=config.service_name,
    enable_metrics=True,
    metrics_path="/metrics"
)

# Add routers
app.include_router(create_health_router(config.service_name), prefix="/health", tags=["Health"])
app.include_router(merchants_router, prefix="/api/v1", tags=["Merchants"])