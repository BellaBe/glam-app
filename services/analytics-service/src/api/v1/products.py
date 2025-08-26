# services/analytics/src/api/v1/products.py
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
from ...schemas.responses import ProductPerformanceData

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get(
    "/products",
    response_model=ApiResponse[ProductPerformanceData],
    status_code=status.HTTP_200_OK,
    summary="Get product performance"
)
async def get_product_performance(
    svc: AnalyticsServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep,
    limit: int = Query(20, ge=1, le=100, description="Number of top products")
):
    """
    Get product performance analytics showing top performing products.
    """
    # Validate shop context
    validate_shop_context(
        client_auth=auth,
        platform_ctx=platform,
        logger=logger,
        expected_scope="analytics:read"
    )
    
    # Get product data
    product_data = await svc.get_product_performance(
        merchant_id=UUID(auth.shop),
        limit=limit,
        correlation_id=ctx.correlation_id
    )
    
    return success_response(
        data=product_data,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )