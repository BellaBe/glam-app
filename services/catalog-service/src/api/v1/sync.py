# services/catalog-service/src/api/v1/sync.py
from fastapi import APIRouter, Body, status

from shared.api import ApiResponse, success_response
from shared.api.dependencies import ClientAuthDep, PlatformContextDep, RequestContextDep
from shared.api.validation import validate_shop_context

from ...dependencies import CatalogServiceDep, EventPublisherDep
from ...schemas.sync import SyncOperationOut, SyncProgressOut, SyncRequestBody

router = APIRouter(prefix="/api/v1/catalog", tags=["Catalog Sync"])


@router.post(
    "/sync",
    response_model=ApiResponse[SyncOperationOut],
    status_code=status.HTTP_201_CREATED,
    summary="Start catalog sync",
)
async def start_sync(
    svc: CatalogServiceDep,
    publisher: EventPublisherDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    body: SyncRequestBody = Body(...),
):
    """
    Start catalog sync operation.
    Returns sync_id for polling progress.
    """

    # Validate shop context
    validate_shop_context(client_auth=auth, platform_ctx=platform, logger=svc.logger, expected_scope="bff:call")

    # Start sync operation
    sync = await svc.start_sync(
        merchant_id=auth.shop,  # Using shop as merchant_id
        platform_name=platform.platform,
        platform_shop_id=platform.domain,  # Using domain as platform_shop_id for now
        domain=platform.domain,
        sync_type=body.sync_type,
        correlation_id=ctx.correlation_id,
    )

    # Publish sync requested event
    await publisher.catalog_sync_requested(
        merchant_id=auth.shop,
        platform_name=platform.platform,
        platform_shop_id=platform.domain,
        domain=platform.domain,
        sync_id=sync.id,
        sync_type=body.sync_type,
        correlation_id=ctx.correlation_id,
    )

    return success_response(data=sync, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@router.get("/sync/{sync_id}", response_model=ApiResponse[SyncProgressOut], summary="Get sync progress")
async def get_sync_progress(
    sync_id: str, svc: CatalogServiceDep, ctx: RequestContextDep, auth: ClientAuthDep, platform: PlatformContextDep
):
    """
    Get sync operation progress for polling.
    Frontend should poll this endpoint to track sync progress.
    """

    # Validate shop context
    validate_shop_context(client_auth=auth, platform_ctx=platform, logger=svc.logger, expected_scope="bff:call")

    # Get progress
    progress = await svc.get_sync_progress(sync_id=sync_id, correlation_id=ctx.correlation_id)

    return success_response(data=progress, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@router.get("/status", response_model=ApiResponse[dict], summary="Get catalog status")
async def get_catalog_status(
    svc: CatalogServiceDep, ctx: RequestContextDep, auth: ClientAuthDep, platform: PlatformContextDep
):
    """Get current catalog status for merchant"""

    # Validate shop context
    validate_shop_context(client_auth=auth, platform_ctx=platform, logger=svc.logger, expected_scope="bff:call")

    # Get status
    status_data = await svc.get_catalog_status(merchant_id=auth.shop, correlation_id=ctx.correlation_id)

    return success_response(data=status_data, request_id=ctx.request_id, correlation_id=ctx.correlation_id)
