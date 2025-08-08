from fastapi import APIRouter
from .v1 import health, credits

router = APIRouter()

# Include v1 routers
router.include_router(health.router)
router.include_router(credits.router)

