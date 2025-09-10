from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.api import setup_middleware
from shared.api.handlers import register_exception_handlers
from shared.api.health import create_health_router
from shared.utils.logger import create_logger

from .api import api_router
from .config import get_service_config
from .lifecycle import ServiceLifecycle

# Global singletons
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
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=config.service_name,
        version=config.service_version,
        description=config.service_description,
        lifespan=lifespan,
    )

    setup_middleware(app, service_name=config.service_name)
    register_exception_handlers(app)

    # Include routers
    app.include_router(create_health_router(config.service_name, prefix="/api/v1/merchants"))
    app.include_router(api_router)

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host=config.api_host, port=config.api_port, reload=config.debug, workers=1)
