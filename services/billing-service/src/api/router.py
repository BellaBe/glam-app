
from fastapi import APIRouter
from .v1 import trials, purchases, billing


api_router = APIRouter()

# Include v1 routers
api_router.include_router(trials.router)
api_router.include_router(purchases.router)
api_router.include_router(billing.router)


