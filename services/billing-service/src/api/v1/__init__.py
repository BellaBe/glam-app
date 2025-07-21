# glam-app/services/billing-service/src/api/v1/__init__.py
"""API v1 package for billing service."""

from fastapi import APIRouter
from . import health, plans, subscriptions, payments, trials

router = APIRouter()

router.include_router(health.router, prefix="/billing")
router.include_router(plans.router, prefix="/billing")
router.include_router(subscriptions.router, prefix="/billing")
router.include_router(trials.router, prefix="/billing")
router.include_router(payments.router, prefix="/billing")

__all__ = ["router"]