from fastapi import APIRouter
from .v1.analytics import router as analytics_router
from .v1.alerts import router as alerts_router
from .v1.platform import router as platform_router

router = APIRouter()

# Include all v1 API routes
router.include_router(analytics_router)
router.include_router(alerts_router)
router.include_router(platform_router)


