# services/analytics/src/api/v1/summary.py
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, status
from shared.api import ApiResponse, success_response
from shared.api.dependencies import (
    RequestContextDep,
    ClientAuthDep,
    PlatformContextDep
)
from shared.api.validation import validate_shop_context
from ...dependencies import AnalyticsServiceDep, LoggerDep
from ...schemas.responses import SummaryResponse, SummaryMeta

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get(
    "/summary",
    response_model=ApiResponse[SummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get analytics summary"
)
async def get_analytics_summary(
    svc: AnalyticsServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep
):
    """
    Get comprehensive analytics summary for merchant.
    Returns today's metrics and last 30 days aggregated data.
    """
    # Validate shop context
    validate_shop_context(
        client_auth=auth,
        platform_ctx=platform,
        logger=logger,
        expected_scope="analytics:read"
    )
    
    # Get summary data
    summary_data = await svc.get_summary_analytics(
        merchant_id=UUID(auth.shop),
        platform_shop_id=platform.domain,
        correlation_id=ctx.correlation_id
    )
    
    # Create response with metadata
    response = SummaryResponse(
        data=summary_data,
        meta=SummaryMeta(
            merchant_id=auth.shop,
            platform_shop_id=platform.domain,
            generated_at=datetime.utcnow()
        )
    )
    
    return success_response(
        data=response,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )
