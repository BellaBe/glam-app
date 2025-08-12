from fastapi import APIRouter
from .v1 import webhooks


router = APIRouter(prefix="/api")

# Include v1 routers
router.include_router(webhooks.router, tags=["webhooks"])
