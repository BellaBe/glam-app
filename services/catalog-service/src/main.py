# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.api import setup_middleware
from shared.api.health import create_health_router
from .config import config
from .lifecycle import CatalogServiceLifecycle
from .api.router import router

# Create lifecycle manager
lifecycle = CatalogServiceLifecycle(config)

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
    title="Catalog Service",
    version=config.service_version,
    description="Product catalog management with sync orchestration and AI analysis coordination",
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
app.include_router(create_health_router(config.service_name))
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.effective_port,
        reload=config.debug,
        log_level=config.logging_level.lower()
    )
