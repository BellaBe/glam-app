# services/notification-service/src/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.api import create_health_router, setup_middleware
from shared.api.handlers import register_exception_handlers
from shared.utils import create_logger

from .api import api_router
from .config import get_service_config
from .lifecycle import ServiceLifecycle

# Create singletons at module level
config = get_service_config()
logger = create_logger(config.service_name)
lifecycle = ServiceLifecycle(config, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan management for startup/shutdown"""
    app.state.lifecycle = lifecycle
    app.state.config = config
    app.state.logger = logger

    try:
        await lifecycle.startup()
        yield
    finally:
        await lifecycle.shutdown()


def create_application() -> FastAPI:
    """Create FastAPI app with shared package integration"""
    app = FastAPI(
        title=config.service_name,
        version=config.service_version,
        description=config.service_description,
        lifespan=lifespan,
    )

    # Setup shared middleware (handles ALL errors)
    setup_middleware(app, service_name=config.service_name)
    register_exception_handlers(app)

    # Add health check from shared package
    app.include_router(create_health_router(config.service_name, prefix="/api/v1/notifications"))
    app.include_router(api_router)

    return app


app = create_application()