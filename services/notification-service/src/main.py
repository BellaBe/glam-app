# File: services/notification-service/src/main.py
"""Main entry point for the Notification Service"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import get_service_config
from .lifecycle import ServiceLifecycle
from .middlewares import add_middleware
from .routers import health, notifications, templates, preferences

# Load configuration
config = get_service_config()

# Create lifecycle manager
lifecycle = ServiceLifecycle(config)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan adapter"""
    # Store lifecycle in app state for access in dependencies
    app.state.lifecycle = lifecycle
    
    await lifecycle.startup()
    try:
        yield
    finally:
        await lifecycle.shutdown()

def create_application() -> FastAPI:
    app = FastAPI(
        title=config.SERVICE_NAME,
        version=config.SERVICE_VERSION,
        lifespan=lifespan,
        description="Email notification service for GlamYouUp platform",
        # Disable default exception handlers as shared middleware handles them
        exception_handlers={}
    )
    
    # Store config for middleware/dependencies
    app.state.config = config
    
    # Add middleware (uses shared components)
    add_middleware(app, config)
    
    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(templates.router, prefix="/api/v1")
    app.include_router(preferences.router, prefix="/api/v1")
    
    return app

app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.API_PORT,
        reload=config.DEBUG
    )