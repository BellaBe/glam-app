# services/analytics/src/api/v1/seasons.py
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
from ...schemas.responses import SeasonDistributionData

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get(
    "/seasons",
    response_model=ApiResponse[SeasonDistributionData],
    status_code=status.HTTP_200_OK,
    summary="Get season distribution"
)
async def get_season_distribution(
    svc: AnalyticsServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep,
    period: str = Query("30d", regex="^(7d|30d)$", description="Time period")
):
    """
    Get season distribution analytics showing shopper season breakdown.
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
    
    # Get season data
    season_data = await svc.get_season_distribution(
        merchant_id=UUID(auth.shop),
        period_days=period_days,
        correlation_id=ctx.correlation_id
    )
    
    return success_response(
        data=season_data,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )