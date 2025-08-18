# services/webhook-service/src/api/v1/__init__.py
from fastapi import APIRouter

from .webhooks import webhooks_router

v1_router = APIRouter(prefix="/v1")

# Include v1 API routes
v1_router.include_router(webhooks_router, tags=["webhooks"])
