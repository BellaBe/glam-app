# services/analytics/src/api/v1/credits.py
from uuid import UUID
from fastapi import APIRouter, status
from shared.api import ApiResponse, success_response
from shared.api.dependencies import (
    RequestContextDep,
    ClientAuthDep,
    PlatformContextDep
)
from shared.api.validation import validate_shop_context
from ...dependencies import AnalyticsServiceDep, LoggerDep
from ...schemas.responses import CreditAnalyticsData

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get(
    "/credits",
    response_model=ApiResponse[CreditAnalyticsData],
    status_code=status.HTTP_200_OK,
    summary="Get credit usage analytics"
)
async def get_credit_analytics(
    svc: AnalyticsServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep
):
    """
    Get credit usage analytics and projections.
    """
    # Validate shop context
    validate_shop_context(
        client_auth=auth,
        platform_ctx=platform,
        logger=logger,
        expected_scope="analytics:read"
    )
    
    # Get credit data
    credit_data = await svc.get_credit_analytics(
        merchant_id=UUID(auth.shop),
        correlation_id=ctx.correlation_id
    )
    
    return success_response(
        data=credit_data,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )