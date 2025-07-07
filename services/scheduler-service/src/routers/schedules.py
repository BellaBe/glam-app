# services/scheduler-service/src/routers/schedules.py
"""Schedule management endpoints"""

from fastapi import APIRouter, Query, HTTPException, Header
from typing import List, Optional
from uuid import UUID

from shared.api import (
    ApiResponse,
    success_response,
    paginated_response,
    Links,
    RequestContextDep,
    PaginationDep
)
from shared.api.correlation import get_correlation_context

from ..dependencies import ScheduleServiceDep, ScheduleRepoDep
from ..schemas import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleDetailResponse,
    ScheduleListResponse,
    ScheduleBulkCreate,
    ScheduleBulkOperation,
    ScheduleTrigger
)
from ..mappers.schedule_mapper import ScheduleMapper
from ..exceptions import ScheduleNotFoundError, ScheduleAlreadyExistsError

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[ScheduleDetailResponse],
    status_code=201,
    summary="Create a new schedule"
)
async def create_schedule(
    schedule_data: ScheduleCreate,
    svc: ScheduleServiceDep,
    ctx: RequestContextDep,
    x_created_by: Optional[str] = Header(None, alias="X-Created-By")
):
    """
    Create a new schedule.
    
    The schedule will be automatically registered with the scheduler
    and will start executing according to its configuration.
    """
    # Get creator from header or context
    created_by = x_created_by or ctx.user_id or "unknown"
    
    try:
        # Convert to command payload
        from shared.events.scheduler.types import CreateScheduleCommandPayload
        command_payload = CreateScheduleCommandPayload(**schedule_data.model_dump())
        
        # Create schedule
        schedule = await svc.create_schedule(
            create_data=command_payload,
            created_by=created_by,
            correlation_id=ctx.correlation_id
        )
        
        # Map to response
        mapper = ScheduleMapper()
        response = mapper.model_to_detail_response(schedule)
        
        return success_response(
            data=response,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            links=Links(self=f"/api/v1/schedules/{schedule.id}")
        )
        
    except ScheduleAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=ApiResponse[ScheduleListResponse],
    summary="List schedules"
)
async def list_schedules(
    svc: ScheduleServiceDep,
    pagination: PaginationDep,
    ctx: RequestContextDep,
    creator: Optional[str] = Query(None, description="Filter by creator"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active state")
):
    """
    List schedules with optional filters.
    
    Supports filtering by creator, tags, status, and active state.
    """
    # Get schedules
    schedules, total = await svc.list_schedules(
        offset=pagination.offset,
        limit=pagination.limit,
        creator=creator,
        tags=tags,
        status=status,
        is_active=is_active
    )
    
    # Map to responses
    mapper = ScheduleMapper()
    schedule_responses = [mapper.model_to_response(s) for s in schedules]
    
    return paginated_response(
        data=schedule_responses,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        base_url="/api/v1/schedules",
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        creator=creator,
        tags=tags,
        status=status,
        is_active=is_active
    )


@router.get(
    "/{schedule_id}",
    response_model=ApiResponse[ScheduleDetailResponse],
    summary="Get schedule details"
)
async def get_schedule(
    schedule_id: UUID,
    svc: ScheduleServiceDep,
    ctx: RequestContextDep
):
    """Get detailed information about a specific schedule."""
    try:
        schedule = await svc.get_schedule(schedule_id)
        
        mapper = ScheduleMapper()
        response = mapper.model_to_detail_response(schedule)
        
        return success_response(
            data=response,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            links=Links(
                self=f"/api/v1/schedules/{schedule_id}",
                executions=f"/api/v1/schedules/{schedule_id}/executions"
            )
        )
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found")


@router.put(
    "/{schedule_id}",
    response_model=ApiResponse[ScheduleDetailResponse],
    summary="Update a schedule"
)
async def update_schedule(
    schedule_id: UUID,
    update_data: ScheduleUpdate,
    svc: ScheduleServiceDep,
    ctx: RequestContextDep,
    x_updated_by: Optional[str] = Header(None, alias="X-Updated-By")
):
    """
    Update an existing schedule.
    
    Only provided fields will be updated. If schedule timing is changed,
    it will be re-registered with the scheduler.
    """
    # Get updater from header or context
    updated_by = x_updated_by or ctx.user_id or "unknown"
    
    try:
        # Convert to command payload
        from shared.events.scheduler.types import UpdateScheduleCommandPayload
        command_payload = UpdateScheduleCommandPayload(
            schedule_id=schedule_id,
            **update_data.model_dump(exclude_unset=True)
        )
        
        # Update schedule
        schedule = await svc.update_schedule(
            schedule_id=schedule_id,
            update_data=command_payload,
            updated_by=updated_by,
            correlation_id=ctx.correlation_id
        )
        
        # Map to response
        mapper = ScheduleMapper()
        response = mapper.model_to_detail_response(schedule)
        
        return success_response(
            data=response,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            links=Links(self=f"/api/v1/schedules/{schedule_id}")
        )
        
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{schedule_id}",
    status_code=204,
    summary="Delete a schedule"
)
async def delete_schedule(
    schedule_id: UUID,
    svc: ScheduleServiceDep,
    ctx: RequestContextDep,
    hard_delete: bool = Query(False, description="Permanently delete schedule"),
    x_deleted_by: Optional[str] = Header(None, alias="X-Deleted-By")
):
    """
    Delete a schedule.
    
    By default performs a soft delete. Set hard_delete=true to permanently remove.
    """
    # Get deleter from header or context
    deleted_by = x_deleted_by or ctx.user_id or "unknown"
    
    try:
        await svc.delete_schedule(
            schedule_id=schedule_id,
            deleted_by=deleted_by,
            hard_delete=hard_delete,
            correlation_id=ctx.correlation_id
        )
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found")


@router.post(
    "/{schedule_id}/pause",
    response_model=ApiResponse[ScheduleDetailResponse],
    summary="Pause a schedule"
)
async def pause_schedule(
    schedule_id: UUID,
    svc: ScheduleServiceDep,
    ctx: RequestContextDep,
    reason: Optional[str] = Query(None, description="Reason for pausing"),
    x_paused_by: Optional[str] = Header(None, alias="X-Paused-By")
):
    """Pause schedule execution."""
    paused_by = x_paused_by or ctx.user_id or "unknown"
    
    try:
        schedule = await svc.pause_schedule(
            schedule_id=schedule_id,
            paused_by=paused_by,
            reason=reason,
            correlation_id=ctx.correlation_id
        )
        
        mapper = ScheduleMapper()
        response = mapper.model_to_detail_response(schedule)
        
        return success_response(
            data=response,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            links=Links(self=f"/api/v1/schedules/{schedule_id}")
        )
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found")


@router.post(
    "/{schedule_id}/resume",
    response_model=ApiResponse[ScheduleDetailResponse],
    summary="Resume a paused schedule"
)
async def resume_schedule(
    schedule_id: UUID,
    svc: ScheduleServiceDep,
    ctx: RequestContextDep,
    x_resumed_by: Optional[str] = Header(None, alias="X-Resumed-By")
):
    """Resume a paused schedule."""
    resumed_by = x_resumed_by or ctx.user_id or "unknown"
    
    try:
        schedule = await svc.resume_schedule(
            schedule_id=schedule_id,
            resumed_by=resumed_by,
            correlation_id=ctx.correlation_id
        )
        
        mapper = ScheduleMapper()
        response = mapper.model_to_detail_response(schedule)
        
        return success_response(
            data=response,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            links=Links(self=f"/api/v1/schedules/{schedule_id}")
        )
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found")


@router.post(
    "/{schedule_id}/trigger",
    response_model=ApiResponse[dict],
    summary="Trigger immediate execution"
)
async def trigger_schedule(
    schedule_id: UUID,
    trigger_data: Optional[ScheduleTrigger] = None,
    svc: ScheduleServiceDep = None,
    ctx: RequestContextDep = None,
    x_triggered_by: Optional[str] = Header(None, alias="X-Triggered-By")
):
    """Trigger a schedule to run immediately."""
    triggered_by = x_triggered_by or ctx.user_id or "unknown"
    
    try:
        execution_id = await svc.trigger_schedule(
            schedule_id=schedule_id,
            triggered_by=triggered_by,
            override_payload=trigger_data.override_payload if trigger_data else None,
            correlation_id=ctx.correlation_id
        )
        
        return success_response(
            data={
                "execution_id": str(execution_id),
                "message": "Schedule triggered successfully"
            },
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            links=Links(
                execution=f"/api/v1/executions/{execution_id}"
            )
        )
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found")


# Bulk operations
@router.post(
    "/bulk/create",
    response_model=ApiResponse[dict],
    summary="Bulk create schedules"
)
async def bulk_create_schedules(
    bulk_data: ScheduleBulkCreate,
    svc: ScheduleServiceDep,
    ctx: RequestContextDep,
    x_created_by: Optional[str] = Header(None, alias="X-Created-By")
):
    """Create multiple schedules in a single request."""
    created_by = x_created_by or ctx.user_id or "unknown"
    
    # Convert to command payloads
    from shared.events.scheduler.types import CreateScheduleCommandPayload
    command_payloads = [
        CreateScheduleCommandPayload(**schedule.model_dump())
        for schedule in bulk_data.schedules
    ]
    
    try:
        created_schedules = await svc.bulk_create(
            schedules=command_payloads,
            created_by=created_by,
            correlation_id=ctx.correlation_id
        )
        
        return success_response(
            data={
                "created": len(created_schedules),
                "schedule_ids": [str(s.id) for s in created_schedules]
            },
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/bulk/operation",
    response_model=ApiResponse[dict],
    summary="Perform bulk operation on schedules"
)
async def bulk_schedule_operation(
    bulk_op: ScheduleBulkOperation,
    svc: ScheduleServiceDep,
    ctx: RequestContextDep,
    x_performed_by: Optional[str] = Header(None, alias="X-Performed-By")
):
    """
    Perform a bulk operation on multiple schedules.
    
    Supported operations: pause, resume, delete
    """
    performed_by = x_performed_by or ctx.user_id or "unknown"
    
    try:
        results = await svc.bulk_operation(
            schedule_ids=bulk_op.schedule_ids,
            operation=bulk_op.operation,
            performed_by=performed_by,
            reason=bulk_op.reason,
            correlation_id=ctx.correlation_id
        )
        
        return success_response(
            data=results,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Schedule executions sub-resource
@router.get(
    "/{schedule_id}/executions",
    response_model=ApiResponse[List[dict]],
    summary="Get schedule executions"
)
async def get_schedule_executions(
    schedule_id: UUID,
    schedule_repo: ScheduleRepoDep,
    ctx: RequestContextDep,
    pagination: PaginationDep,
    status: Optional[str] = Query(None, description="Filter by execution status")
):
    """Get execution history for a specific schedule."""
    # Import here to avoid circular dependency
    from ..repositories.execution_repository import ExecutionRepository
    from ..mappers.execution_mapper import ExecutionMapper
    
    # Check schedule exists
    schedule = await schedule_repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Get executions through repository directly
    # (In a real implementation, this would be injected)
    execution_repo = ExecutionRepository(schedule_repo.db_manager)
    
    executions = await execution_repo.get_by_schedule(
        schedule_id=schedule_id,
        offset=pagination.offset,
        limit=pagination.limit,
        status=status
    )
    
    # Map to responses
    mapper = ExecutionMapper()
    execution_responses = [mapper.model_to_response(e) for e in executions]
    
    return paginated_response(
        data=execution_responses,
        page=pagination.page,
        limit=pagination.limit,
        total=len(executions),  # Simplified - would need proper count
        base_url=f"/api/v1/schedules/{schedule_id}/executions",
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        status=status
    )