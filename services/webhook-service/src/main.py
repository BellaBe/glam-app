# services/webhook-service/src/main.py
"""
Webhook service FastAPI application.

Entry point for the webhook service that receives and processes
external webhooks from various platforms.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.api.error_handlers import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from shared.api.middleware import (
    RequestLoggingMiddleware,
    CorrelationIdMiddleware,
    MetricsMiddleware
)
from shared.monitoring.metrics import init_metrics

from .config import get_config
from .lifecycle import ServiceLifecycle
from .api.v1 import health, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    config = get_config()
    lifecycle = ServiceLifecycle(config)
    
    await lifecycle.startup()
    
    # Store in app state
    app.state.lifecycle = lifecycle
    app.state.config = config
    
    # Initialize metrics
    init_metrics(service_name=config.SERVICE_NAME)
    
    yield
    
    # Shutdown
    await lifecycle.shutdown()


# Create FastAPI app
app = FastAPI(
    title="Webhook Service",
    description="Unified webhook ingestion service for GlamYouUp platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "webhook-service",
        "version": "2.0.0",
        "status": "operational"
    }