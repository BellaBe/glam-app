from fastapi import APIRouter, Depends
from typing import Annotated
from datetime import datetime
from shared.api import success_response, RequestContextDep
from shared.errors import GlamBaseError
from ..dependencies import get_email_service
from ..services.email_service import EmailService
from shared.database import get_database_health

router = APIRouter()

@router.get("/health")
async def health_check(
    ctx: RequestContextDep
):
    """Basic health check"""
    return success_response(
        data={
            "status": "healthy",
            "service": "notification-service",
            "timestamp": datetime.utcnow().isoformat()
        },
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

@router.get("/health/detailed")
async def detailed_health_check(
    ctx: RequestContextDep,
    email_service: Annotated[EmailService, Depends(get_email_service)]
):
    """Detailed health check including dependencies"""
    health_data = {
        "status": "healthy",
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        db_health = await get_database_health()
        health_data["checks"]["database"] = {
            "status": "healthy" if db_health else "unhealthy",
            "responsive": db_health
        }
    except Exception as e:
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # Check email providers
    try:
        provider_health = await email_service.health_check()
        health_data["checks"]["email_providers"] = provider_health
        
        # If no providers are healthy, service is degraded
        if not any(provider_health.values()):
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["checks"]["email_providers"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # If service is unhealthy, raise an error to trigger 503
    if health_data["status"] != "healthy":
        raise GlamBaseError(
            code="SERVICE_DEGRADED",
            message="Service is degraded",
            status=503,
            details=health_data
        )
    
    return success_response(
        data=health_data,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

@router.get("/ready")
async def readiness_check(
    ctx: RequestContextDep
):
    """Kubernetes readiness probe"""
    return success_response(
        data={"ready": True},
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

@router.get("/live")
async def liveness_check(
    ctx: RequestContextDep
):
    """Kubernetes liveness probe"""
    return success_response(
        data={"alive": True},
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )