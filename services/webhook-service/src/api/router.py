from fastapi import APIRouter
from .v1 import webhooks


router = APIRouter()

# Include v1 routers
router.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])


