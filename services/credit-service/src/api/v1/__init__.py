# services/credit-service/src/api/v1/__init__.py
"""API v1 package for credit service."""

from fastapi import APIRouter
from . import health, accounts, transactions, plugin_status

# Create main v1 router
router = APIRouter(prefix="/api/v1")

# Include all v1 routers
router.include_router(health.router)
router.include_router(accounts.router, prefix="/credits") 
router.include_router(transactions.router, prefix="/credits")
router.include_router(plugin_status.router, prefix="/credits")

__all__ = ["router"]