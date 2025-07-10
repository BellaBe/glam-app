# services/credit-service/src/main.py
"""
Credit Service main application.

Follows the same pattern as notification service.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from shared.utils.logger import create_logger
from shared.api.middleware import RequestContextMiddleware
from shared.errors import setup_exception_handlers

from .config import get_config
from .lifecycle import ServiceLifecycle
from .api.v1 import health, accounts, transactions, plugin_status
from .exceptions import *  # Import all exceptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    config = get_config()
    logger = create_logger(config.SERVICE_NAME, config.LOG_LEVEL)
    
    logger.info("Starting Credit Service", version="1.0.0")
    
    # Initialize service lifecycle
    lifecycle = ServiceLifecycle(config, logger)
    
    try:
        # Start all services
        await lifecycle.startup()
        
        # Store in app state
        app.state.lifecycle = lifecycle
        app.state.config = config
        
        logger.info("Credit Service started successfully")
        
        yield
        
    finally:
        logger.info("Shutting down Credit Service")
        await lifecycle.shutdown()
        logger.info("Credit Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Credit Service",
    description="Credit management service for merchant credits and plugin access control",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestContextMiddleware)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1/credits")
app.include_router(transactions.router, prefix="/api/v1/credits")
app.include_router(plugin_status.router, prefix="/api/v1/credits")

# Add metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=config.SERVICE_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )