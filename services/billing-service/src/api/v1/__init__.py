# services/billing-service/src/api/v1/__init__.py
from fastapi import APIRouter

from .billing import billing_router
from .purchases import purchases_router
from .trials import trials_router

v1_router = APIRouter()
v1_router.include_router(billing_router, prefix="/billing", tags=["billing"])
v1_router.include_router(purchases_router, prefix="/billing/purchases", tags=["purchases"])
v1_router.include_router(trials_router, prefix="/billing/trials", tags=["trials"])
