from fastapi import APIRouter
from .webhooks import router as webhooks_router

router = APIRouter(prefix="/v1")

# Include v1 API routes
router.include_router(webhooks_router, tags=["webhooks"])
