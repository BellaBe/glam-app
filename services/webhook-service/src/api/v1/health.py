# glam-app/services/webhook-service/src/api/v1/health.py

from fastapi import APIRouter
from shared.api.health import create_health_router

router = APIRouter()

# Include reusable shared health routes for this service
health_router = create_health_router("webhook-service")
router.include_router(health_router)