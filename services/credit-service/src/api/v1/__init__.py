# services/credit-service/src/api/v1/__init__.py
"""API v1 package for credit service."""

from fastapi import APIRouter
from . import health, credits, transactions, plugin_status

# Create main v1 router
router = APIRouter()

# Include all v1 routers
router.include_router(health.router)
router.include_router(credits.router, prefix="/credits") 
router.include_router(transactions.router, prefix="/credits")
router.include_router(plugin_status.router, prefix="/credits")

__all__ = ["router"]