from fastapi import APIRouter
from .v1 import merchants

router = APIRouter()

# Include v1 routes
router.include_router(merchants.router, tags=["merchants"])

