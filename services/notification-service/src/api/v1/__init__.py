# services/notification-service/src/api/v1/__init__.py
from fastapi import APIRouter

from .notifications import notifications_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(notifications_router, tags=["notifications"])
