# services/selfie-service/src/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.api import create_health_router, setup_middleware
from shared.utils import create_logger

from .config import get_service_config
from .lifecycle import ServiceLifecycle
from .tasks import start_cleanup_sweeper

# Create singletons
config = get_service_config()
logger = create_logger(config.service_name)
lifecycle = ServiceLifecycle(config, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan management"""
    app.state.lifecycle = lifecycle
    app.state.config = config
    app.state.logger = logger  # Required for middleware

    try:
        await lifecycle.startup()
        # Start background cleanup sweeper
        app.state.sweeper_task = await start_cleanup_sweeper(lifecycle, logger)
        yield
    finally:
        if hasattr(app.state, "sweeper_task"):
            app.state.sweeper_task.cancel()
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

    # CORS for direct upload from widget
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Shop-Domain", "X-Shop-Platform", "If-None-Match"],
        expose_headers=["ETag"],
        max_age=86400,
    )

    # Add health check
    app.include_router(create_health_router(config.service_name))

    # Add API routes
    from .api.v1 import analyses

    app.include_router(analyses.router)

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host=config.api_host, port=config.api_port, reload=config.debug)
