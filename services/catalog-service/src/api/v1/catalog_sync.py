from fastapi import APIRouter, status, HTTPException, Header
from typing import Optional
from shared.api import ApiResponse, success_response, error_response
from shared.api.dependencies import RequestContextDep
from ...dependencies import (
    CatalogSyncServiceDep,
    AuthDep,
    ShopDomainDep
)
from ...schemas.catalog_sync import (
    SyncRequestIn,
    SyncAllowedOut,
    SyncCreatedOut,
    SyncStatusOut,
    SyncJobOut
)
from ...exceptions import (
    SyncNotAllowedError,
    SyncAlreadyActiveError,
    InvalidSyncTypeError,
    SyncNotFoundError
)

router = APIRouter()

@router.get(
    "/catalog/sync/allowed",
    response_model=ApiResponse[SyncAllowedOut],
    summary="Check if sync is allowed",
    description="Pre-flight check to determine if catalog sync can be started"
)
async def check_sync_allowed(
    service: CatalogSyncServiceDep,
    ctx: RequestContextDep,
    _auth: AuthDep,
    shop_domain: ShopDomainDep
) -> ApiResponse[SyncAllowedOut]:
    """Check if sync is allowed for the merchant"""
    result = await service.check_sync_allowed(shop_domain)
    return success_response(
        data=result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

@router.post(
    "/catalog/sync",
    response_model=ApiResponse[SyncCreatedOut],
    status_code=status.HTTP_201_CREATED,
    summary="Start catalog sync",
    description="Initiate a new catalog synchronization"
)
async def start_sync(
    service: CatalogSyncServiceDep,
    ctx: RequestContextDep,
    _auth: AuthDep,
    shop_domain: ShopDomainDep,
    body: SyncRequestIn,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
) -> ApiResponse[SyncCreatedOut]:
    """Start a new catalog sync"""
    try:
        sync_id = await service.start_sync(shop_domain, body.type)
        return success_response(
            data=SyncCreatedOut(syncId=sync_id),
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id
        )
    except SyncNotAllowedError as e:
        return error_response(
            code="SYNC_NOT_ALLOWED",
            message=str(e),
            details={"reason": e.message},
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            status_code=403
        )
    except SyncAlreadyActiveError as e:
        return error_response(
            code="SYNC_ALREADY_ACTIVE",
            message=str(e),
            details={"activeSyncId": e.current_state},
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            status_code=409
        )
    except InvalidSyncTypeError as e:
        return error_response(
            code="INVALID_SYNC_TYPE",
            message=str(e),
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            status_code=422
        )

@router.get(
    "/catalog/sync/status",
    response_model=ApiResponse[SyncStatusOut],
    summary="Get sync status",
    description="Get current synchronization status for the merchant"
)
async def get_sync_status(
    service: CatalogSyncServiceDep,
    ctx: RequestContextDep,
    _auth: AuthDep,
    shop_domain: ShopDomainDep
) -> ApiResponse[SyncStatusOut]:
    """Get current sync status"""
    result = await service.get_sync_status(shop_domain)
    return success_response(
        data=result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

@router.get(
    "/catalog/sync/{sync_id}",
    response_model=ApiResponse[SyncJobOut],
    summary="Get sync job details",
    description="Get details of a specific sync job"
)
async def get_sync_job(
    sync_id: str,
    service: CatalogSyncServiceDep,
    ctx: RequestContextDep,
    _auth: AuthDep,
    shop_domain: ShopDomainDep
) -> ApiResponse[SyncJobOut]:
    """Get specific sync job details"""
    # This endpoint would need implementation in the service
    # For now, return not implemented
    raise HTTPException(
        status_code=501,
        detail="Get sync job by ID not yet implemented"
    )

# ================================================================
