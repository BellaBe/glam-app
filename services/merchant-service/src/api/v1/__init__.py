from fastapi import APIRouter
from .merchants import router as merchants_router

router = APIRouter(prefix="/api/v1")

# Include v1 API routes
router.include_router(merchants_router, prefix="/merchants")