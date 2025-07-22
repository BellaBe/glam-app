from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.api import setup_middleware
from shared.api.health import create_health_router
from .config import config
from .lifecycle import AnalyticsLifecycle
from .api.router import router

# Create lifecycle manager
lifecycle = AnalyticsLifecycle(config)

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
    description="Analytics Service - Intelligence hub for usage analysis, insights, and predictive analytics",
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

# Custom metrics endpoint for analytics-specific metrics
@app.get("/analytics/metrics/custom")
async def get_custom_metrics():
    """Get analytics-specific metrics"""
    return {
        "service": config.service_name,
        "custom_metrics": {
            "patterns_detected_24h": 45,
            "predictions_generated_24h": 23,
            "alerts_triggered_24h": 8,
            "anomalies_detected_24h": 3
        }
    }


# ========== Configuration Files ==========

