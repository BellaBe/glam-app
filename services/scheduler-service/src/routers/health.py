# services/scheduler-service/src/routers/health.py
"""Health check endpoints"""

from fastapi import APIRouter, Depends
from typing import Annotated
from datetime import datetime, timezone
from shared.api import success_response, RequestContextDep
from shared.database import get_database_health
from ..dependencies import get_scheduler_manager, get_schedule_repository
from ..services.scheduler_manager import SchedulerManager
from ..repositories.schedule_repository import ScheduleRepository

router = APIRouter()


@router.get("/health")
async def health_check(
    ctx: RequestContextDep
):
    """Basic health check"""
    return success_response(
        data={
            "status": "healthy",
            "service": "scheduler-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )


@router.get("/health/detailed")
async def detailed_health_check(
    ctx: RequestContextDep,
    scheduler_manager: Annotated[SchedulerManager, Depends(get_scheduler_manager)],
    schedule_repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)]
):
    """Detailed health check including dependencies"""
    health_data = {
        "status": "healthy",
        "service": "scheduler-service",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {}
    }
    
    # Check database
    try:
        db_health = await get_database_health(schedule_repo.db_manager)
        health_data["dependencies"]["database"] = db_health
    except Exception as e:
        health_data["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # Check scheduler
    try:
        scheduler_running = scheduler_manager._started
        health_data["dependencies"]["scheduler"] = {
            "status": "healthy" if scheduler_running else "unhealthy",
            "running": scheduler_running
        }
        if not scheduler_running:
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["dependencies"]["scheduler"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
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