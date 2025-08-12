from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from shared.api import setup_middleware
from shared.api.health import create_health_router
from shared.utils.logger import create_logger
from .config import get_service_config
from .lifecycle import ServiceLifecycle
from .api import api_router

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
        "api_port": config.api_port,
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
        description=config.service_description,
        docs_url="/docs",
        redoc_url="/redoc",
        exception_handlers={}  # Use shared middleware for exception handling
    )
    
    setup_middleware(
        app,
        service_name=config.service_name,
        enable_metrics=config.monitoring_metrics_enabled,
        metrics_path="/metrics"
    )
    
    # Include routers
    app.include_router(create_health_router(config.service_name))
    app.include_router(api_router)
    
    
    return app

app = create_application()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("[VALIDATION ERROR] ===== Request Validation Failed =====")
    print(f"[VALIDATION ERROR] Path: {request.url.path}")
    print(f"[VALIDATION ERROR] Method: {request.method}")
    
    # Log the raw body if available
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        print(f"[VALIDATION ERROR] Raw Body: {body_str}")
        
        # Try to parse as JSON to pretty print
        try:
            body_json = json.loads(body_str)
            print(f"[VALIDATION ERROR] Parsed Body: {json.dumps(body_json, indent=2)}")
        except:
            pass
    except:
        print("[VALIDATION ERROR] Could not read request body")
    
    # Log validation errors
    print(f"[VALIDATION ERROR] Errors: {exc.errors()}")
    
    # Log specific field issues
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        print(f"[VALIDATION ERROR] Field '{field_path}': {error['msg']} (type: {error['type']})")
    
    # Return the normal error response
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug
    )

