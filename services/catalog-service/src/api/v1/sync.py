# src/api/v1/sync.py
from uuid import UUID
from typing import List
from fastapi import APIRouter, Path, Body, status, HTTPException
from shared.api import ApiResponse, success_response, RequestContextDep
from ...services.sync_service import SyncService
from ...schemas.sync import SyncOperationIn, SyncOperationOut
from ...exceptions import SyncOperationNotFoundError, SyncOperationAlreadyRunningError
from ...dependencies import SyncServiceDep, IdempotencyKeyDep

router = APIRouter(prefix="/api/v1/sync", tags=["Sync Operations"])

@router.post(
    "",
    response_model=ApiResponse[SyncOperationOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create Sync Operation",
)
async def create_sync(
    svc: SyncServiceDep,
    ctx: RequestContextDep,
    idempotency_key: IdempotencyKeyDep,
    body: SyncOperationIn = Body(...),
):
    """Create a new sync operation for a shop"""
    try:
        out = await svc.create_sync(body, idempotency_key, ctx.correlation_id)
        return success_response(out, ctx.request_id, ctx.correlation_id)
    except SyncOperationAlreadyRunningError as e:
        raise HTTPException(409, str(e))

@router.get(
    "/{sync_id}",
    response_model=ApiResponse[SyncOperationOut],
    summary="Get Sync Operation",
)
async def get_sync(
    svc: SyncServiceDep,
    ctx: RequestContextDep,
    sync_id: UUID = Path(...),
):
    """Get sync operation by ID"""
    try:
        out = await svc.get_sync(sync_id)
        return success_response(out, ctx.request_id, ctx.correlation_id)
    except SyncOperationNotFoundError:
        raise HTTPException(404, "Sync operation not found")

@router.get(
    "",
    response_model=ApiResponse[List[SyncOperationOut]],
    summary="List Sync Operations",
)
async def list_syncs(
    svc: SyncServiceDep,
    ctx: RequestContextDep,
    shop_id: str,
    limit: int = 10,
):
    """List sync operations for a shop"""
    out = await svc.list_syncs(shop_id, limit)
    return success_response(out, ctx.request_id, ctx.correlation_id)
