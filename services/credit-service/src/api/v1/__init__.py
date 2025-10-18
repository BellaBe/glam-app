# services/credit-service/src/api/v1/__init__.py
from fastapi import APIRouter
from .credits import credits_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(credits_router, prefix="/credits", tags=["credits"])