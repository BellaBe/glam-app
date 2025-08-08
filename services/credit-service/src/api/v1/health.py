from fastapi import APIRouter, status
from shared.api import ApiResponse, success_response
from ...config import get_service_config

router = APIRouter(tags=["health"])
config = get_service_config()

@router.get(
    "/health",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Health check"
)
async def health_check():
    """Service health check endpoint"""
    return success_response({
        "status": "healthy",
        "service": config.service_name,
        "version": config.service_version,
        "environment": config.environment
    })

