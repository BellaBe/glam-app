from fastapi import APIRouter, status
from shared.api import ApiResponse, success_response
from shared.api.dependencies import RequestContextDep
from ...dependencies import LifecycleDep, ConfigDep

router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    response_model=ApiResponse[dict],
    summary="Health check",
)
async def health_check(
    ctx: RequestContextDep,
    config: ConfigDep,
):
    """Basic health check"""
    return success_response(
        {"status": "healthy", "service": config.service_name},
        ctx.request_id,
        ctx.correlation_id,
    )

@router.get(
    "/health/detailed",
    response_model=ApiResponse[dict],
    summary="Detailed health check",
)
async def detailed_health_check(
    ctx: RequestContextDep,
    lifecycle: LifecycleDep,
):
    """Detailed health check with component status"""
    components = {}
    
    # Check database
    if lifecycle.prisma and lifecycle._db_connected:
        try:
            await lifecycle.prisma.query_raw("SELECT 1")
            components["database"] = {"status": "healthy", "connected": True}
        except Exception as e:
            components["database"] = {"status": "unhealthy", "error": str(e)}
    else:
        components["database"] = {"status": "unhealthy", "connected": False}
    
    # Check Redis
    if lifecycle.redis:
        try:
            await lifecycle.redis.ping()
            components["redis"] = {"status": "healthy", "connected": True}
        except Exception as e:
            components["redis"] = {"status": "unhealthy", "error": str(e)}
    else:
        components["redis"] = {"status": "unhealthy", "connected": False}
    
    # Check NATS
    if lifecycle.messaging_client:
        try:
            # TODO: Add NATS health check
            components["nats"] = {"status": "healthy", "connected": True}
        except Exception as e:
            components["nats"] = {"status": "unhealthy", "error": str(e)}
    else:
        components["nats"] = {"status": "unhealthy", "connected": False}
    
    # Overall status
    overall_status = "healthy" if all(
        c.get("status") == "healthy" for c in components.values()
    ) else "unhealthy"
    
    return success_response(
        {
            "status": overall_status,
            "components": components
        },
        ctx.request_id,
        ctx.correlation_id,
    )

