# services/billing-service/src/api/v1/__init__.py
from fastapi import APIRouter

from .billing import billing_router
v1_router = APIRouter()
v1_router.include_router(billing_router, prefix="/billing", tags=["billing"])