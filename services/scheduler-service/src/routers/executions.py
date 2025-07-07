# services/scheduler-service/src/routers/executions.py
"""Execution history endpoints"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from shared.api import (
    ApiResponse,
    success_response,
    paginated_response,
    Links,
    RequestContextDep,
    PaginationDep
)

from ..dependencies import ExecutionRepoDep, ScheduleRepoDep
from ..schemas import (
    ExecutionResponse,
    ExecutionDetailResponse,
    ExecutionListResponse,
    ExecutionStats
)
from ..mappers.execution_mapper import ExecutionMapper
from ..exceptions import ExecutionNotFoundError

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[ExecutionListResponse],
    summary="List all executions"
)
async def list_executions(
    execution_repo: ExecutionRepoDep,
    pagination: PaginationDep,
    ctx: RequestContextDep,
    schedule_id: Optional[UUID] = Query(None, description="Filter by schedule ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    started_after: Optional[datetime] = Query(None, description="Filter by start time")
):
    """
    List all executions across all schedules.
    
    Supports filtering by schedule, status, and start time.
    """
    filters = []
    
    if schedule_id:
        from ..models.execution import ScheduleExecution
        filters.append(ScheduleExecution.schedule_id == schedule_id)
    
    if status:
        from ..models.execution import ScheduleExecution, ExecutionStatus
        try:
            status_enum = ExecutionStatus(status)
            filters.append(ScheduleExecution.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    if started_after:
        from ..models.execution import ScheduleExecution
        filters.append(ScheduleExecution.started_at >= started_after)
    
    # Get executions
    executions = await execution_repo.get_all(
        offset=pagination.offset,
        limit=pagination.limit,
        filters=filters if filters else None
    )
    
    total = await execution_repo.count(filters if filters else None)
    
    # Map to responses
    mapper = ExecutionMapper()
    execution_responses = [mapper.model_to_response(e) for e in executions]
    
    return paginated_response(
        data=execution_responses,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        base_url="/api/v1/executions",
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        schedule_id=schedule_id,
        status=status,
        started_after=started_after
    )


@router.get(
    "/{execution_id}",
    response_model=ApiResponse[ExecutionDetailResponse],
    summary="Get execution details"
)
async def get_execution(
    execution_id: UUID,
    execution_repo: ExecutionRepoDep,
    ctx: RequestContextDep
):
    """Get detailed information about a specific execution."""
    execution = await execution_repo.get_by_id(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    mapper = ExecutionMapper()
    response = mapper.model_to_detail_response(execution)
    
    return success_response(
        data=response,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        links=Links(
            self=f"/api/v1/executions/{execution_id}",
            schedule=f"/api/v1/schedules/{execution.schedule_id}"
        )
    )


@router.get(
    "/stats/{schedule_id}",
    response_model=ApiResponse[ExecutionStats],
    summary="Get execution statistics for a schedule"
)
async def get_execution_stats(
    schedule_id: UUID,
    execution_repo: ExecutionRepoDep,
    schedule_repo: ScheduleRepoDep,
    ctx: RequestContextDep,
    time_window_hours: Optional[int] = Query(
        None,
        description="Time window in hours for statistics (default: all time)"
    )
):
    """
    Get execution statistics for a specific schedule.
    
    Includes success rate, duration stats, and failure analysis.
    """
    # Check schedule exists
    schedule = await schedule_repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Calculate time window
    time_window = None
    if time_window_hours:
        time_window = timedelta(hours=time_window_hours)
    
    # Get stats
    stats = await execution_repo.get_stats(schedule_id, time_window)
    
    # Add time period stats (simplified - would need proper implementation)
    stats['executions_last_hour'] = 0
    stats['executions_last_24h'] = 0
    stats['executions_last_7d'] = 0
    
    # Map to response
    mapper = ExecutionMapper()
    response = mapper.stats_to_response(
        stats,
        schedule_id,
        schedule.next_run_at
    )
    
    return success_response(
        data=response,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        links=Links(
            schedule=f"/api/v1/schedules/{schedule_id}",
            executions=f"/api/v1/schedules/{schedule_id}/executions"
        )
    )


@router.get(
    "/running",
    response_model=ApiResponse[List[ExecutionResponse]],
    summary="Get currently running executions"
)
async def get_running_executions(
    execution_repo: ExecutionRepoDep,
    ctx: RequestContextDep
):
    """Get all currently running executions."""
    executions = await execution_repo.get_running_executions()
    
    mapper = ExecutionMapper()
    execution_responses = [mapper.model_to_response(e) for e in executions]
    
    return success_response(
        data=execution_responses,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )


@router.get(
    "/by-correlation/{correlation_id}",
    response_model=ApiResponse[ExecutionDetailResponse],
    summary="Get execution by correlation ID"
)
async def get_execution_by_correlation(
    correlation_id: str,
    execution_repo: ExecutionRepoDep,
    ctx: RequestContextDep
):
    """Get execution by correlation ID for tracing."""
    execution = await execution_repo.get_by_correlation_id(correlation_id)
    
    if not execution:
        raise HTTPException(
            status_code=404,
            detail=f"No execution found with correlation ID: {correlation_id}"
        )
    
    mapper = ExecutionMapper()
    response = mapper.model_to_detail_response(execution)
    
    return success_response(
        data=response,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        links=Links(
            self=f"/api/v1/executions/{execution.id}",
            schedule=f"/api/v1/schedules/{execution.schedule_id}"
        )
    )