# services/webhook-service/src/api/v1/health.py
"""Health check endpoints."""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from shared.database.dependencies import get_database_health
from ...dependencies import LifecycleDep


router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    lifecycle: LifecycleDep,
    db_health: Dict[str, Any] = Depends(get_database_health)
) -> Dict[str, Any]:
    """
    Comprehensive health check for webhook service.
    
    Validates:
    - Database connectivity
    - Redis connectivity
    - NATS connectivity
    - Platform secrets presence
    """
    
    health_status = {
        "status": "healthy",
        "service": "webhook-service",
        "checks": {
            "database": db_health["status"],
            "redis": "unknown",
            "nats": "unknown",
            "secrets": "unknown"
        }
    }
    
    # Check Redis
    try:
        if lifecycle.redis_client:
            await lifecycle.redis_client.ping()
            health_status["checks"]["redis"] = "healthy"
        else:
            health_status["checks"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check NATS
    try:
        if lifecycle.messaging_wrapper and lifecycle.messaging_wrapper._client:
            if lifecycle.messaging_wrapper._client.is_connected:
                health_status["checks"]["nats"] = "healthy"
            else:
                health_status["checks"]["nats"] = "unhealthy: disconnected"
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["nats"] = "unhealthy: not initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["nats"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check secrets
    if lifecycle.config.SHOPIFY_WEBHOOK_SECRET:
        health_status["checks"]["secrets"] = "healthy"
    else:
        health_status["checks"]["secrets"] = "unhealthy: missing Shopify secret"
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/health/ready")
async def readiness_check(lifecycle: LifecycleDep) -> Dict[str, str]:
    """Simple readiness check for k8s"""
    
    # Quick checks
    if not lifecycle.webhook_service:
        return {"status": "not_ready", "reason": "service not initialized"}
    
    if not lifecycle.messaging_wrapper or not lifecycle.messaging_wrapper._client.is_connected:
        return {"status": "not_ready", "reason": "messaging not connected"}
    
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """Simple liveness check for k8s"""
    return {"status": "alive"}