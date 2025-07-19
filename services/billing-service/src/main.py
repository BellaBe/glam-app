# services/billing-service/src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from shared.api import setup_middleware
from shared.api.health import create_health_router

# Create lifecycle manager
config = load_config()
lifecycle = BillingServiceLifecycle(config)


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
    description="Billing service for subscription and payment management",
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

# Create main router with dependencies
@app.on_event("startup")
async def setup_routes():
    """Setup routes after lifecycle initialization"""
    main_router = create_main_router(
        billing_service=lifecycle.billing_service,
        trial_service=lifecycle.trial_service,
        purchase_service=lifecycle.purchase_service,
        plan_repo=lifecycle.plan_repo
    )
    app.include_router(main_router)