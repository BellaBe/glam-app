# services/analytics/src/api/v1/shoppers.py
from uuid import UUID
from fastapi import APIRouter, Query, status
from shared.api import ApiResponse, success_response
from shared.api.dependencies import (
    RequestContextDep,
    ClientAuthDep,
    PlatformContextDep
)
from shared.api.validation import validate_shop_context
from ...dependencies import AnalyticsServiceDep, LoggerDep
from ...schemas.responses import ShopperAnalyticsData

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get(
    "/shoppers",
    response_model=ApiResponse[ShopperAnalyticsData],
    status_code=status.HTTP_200_OK,
    summary="Get shopper analytics"
)
async def get_shopper_analytics(
    svc: AnalyticsServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep,
    period: str = Query("7d", regex="^(7d|30d)$", description="Time period")
):
    """
    Get shopper engagement analytics.
    Period can be '7d' for last 7 days or '30d' for last 30 days.
    """
    # Validate shop context
    validate_shop_context(
        client_auth=auth,
        platform_ctx=platform,
        logger=logger,
        expected_scope="analytics:read"
    )
    
    # Parse period
    period_days = 7 if period == "7d" else 30
    
    # Get shopper data
    shopper_data = await svc.get_shopper_analytics(
        merchant_id=UUID(auth.shop),
        period_days=period_days,
        correlation_id=ctx.correlation_id
    )
    
    return success_response(
        data=shopper_data,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )