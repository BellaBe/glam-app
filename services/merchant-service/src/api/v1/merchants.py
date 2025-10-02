# services/merchant-service/src/api/v1/merchants.py
from fastapi import APIRouter, status

from shared.api import ApiResponse, success_response
from shared.api.dependencies import ClientAuthDep, RequestContextDep
from shared.utils.exceptions import ForbiddenError

from ...dependencies import MerchantServiceDep
from ...schemas import MerchantOut, MerchantSyncIn, MerchantSyncOut

merchants_router = APIRouter(prefix="/merchants")


@merchants_router.post(
    "/sync",
    response_model=ApiResponse[MerchantSyncOut],
    status_code=status.HTTP_200_OK,
    summary="Sync merchant from OAuth flow",
    description="Create or update merchant after OAuth completion. Used in afterAuth hooks.",
)
async def sync_merchant(
    data: MerchantSyncIn,
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
):
    """Sync merchant after OAuth completion."""

    if auth.scope not in ["bff:api:access"]:
        raise ForbiddenError(message="Cannot sync merchant", required_permission="bff:api:access")

    platform_name = ctx.platform
    domain = ctx.domain

    result = await service.sync_merchant(data, platform_name, domain, ctx)
    return success_response(result, ctx.correlation_id)


@merchants_router.get(
    "/self",
    response_model=ApiResponse[MerchantOut],
    status_code=status.HTTP_200_OK,
    summary="Get current merchant",
    description="Get current merchant using platform context from headers",
)
async def get_current_merchant(
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
):
    """Get current merchant using platform context from headers."""

    if auth.scope not in ["bff:api:access"]:
        raise ForbiddenError(message="Cannot read merchant", required_permission="bff:api:access")

    merchant = await service.get_merchant(
        domain=ctx.domain,
        platform_name=ctx.platform,
    )

    return success_response(merchant, ctx.correlation_id)
