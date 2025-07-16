# services/webhook-service/src/api/v1/health.py
"""Health check endpoints for webhook service."""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from shared.api.dependencies import RequestIdDep
from shared.database.dependencies import get_database_health

from ...dependencies import LifecycleDep, ConfigDep

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    request_id: RequestIdDep,
    config: ConfigDep
) -> Dict[str, Any]:
    """Basic health check endpoint."""
    
    return {
        "status": "healthy",
        "service": config.service_name,
        "version": config.service_version,
        "request_id": request_id
    }


@router.get("/health/detailed")
async def detailed_health_check(
    request_id: RequestIdDep,
    lifecycle: LifecycleDep,
    config: ConfigDep
) -> Dict[str, Any]:
    """Detailed health check with component status."""
    
    health_data = {
        "status": "healthy",
        "service": config.service_name,
        "version": config.service_version,
        "request_id": request_id,
        "components": {}
    }
    
    # Check database
    if config.db_enabled and lifecycle.db_manager:
        try:
            db_health = await get_database_health()
            health_data["components"]["database"] = {
                "status": "healthy" if db_health["connected"] else "unhealthy",
                "details": db_health
            }
        except Exception as e:
            health_data["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Check Redis
    if lifecycle.redis_client:
        try:
            await lifecycle.redis_client.ping()
            health_data["components"]["redis"] = {"status": "healthy"}
        except Exception as e:
            health_data["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Check NATS
    if lifecycle.messaging_wrapper:
        try:
            is_connected = lifecycle.messaging_wrapper._nats.is_connected
            health_data["components"]["nats"] = {
                "status": "healthy" if is_connected else "unhealthy",
                "connected": is_connected
            }
        except Exception as e:
            health_data["components"]["nats"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Check if any component is unhealthy
    unhealthy_components = [
        name for name, component in health_data["components"].items()
        if component["status"] == "unhealthy"
    ]
    
    if unhealthy_components:
        health_data["status"] = "degraded"
        health_data["unhealthy_components"] = unhealthy_components
    
    return health_data
