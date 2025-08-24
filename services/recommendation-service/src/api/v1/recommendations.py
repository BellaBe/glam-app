# services/recommendation-service/src/api/v1/recommendations.py
from uuid import UUID
from fastapi import APIRouter, Body, status
from shared.api import ApiResponse, success_response
from shared.api.dependencies import (
    RequestContextDep,
    ClientAuthDep,
    PlatformContextDep,
    CorrelationIdDep
)
from shared.api.validation import validate_shop_context
from shared.utils.exceptions import ValidationError

from ...dependencies import (
    RecommendationServiceDep,
    EventPublisherDep,
    LoggerDep
)
from ...schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    MatchOut
)
from ...schemas.events import MatchCompletedPayload, MatchFailedPayload

router = APIRouter(prefix="/api/v1/recommendations", tags=["Recommendations"])


@router.post(
    "",
    response_model=ApiResponse[RecommendationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create product recommendations"
)
async def create_recommendation(
    request: RecommendationRequest = Body(...),
    svc: RecommendationServiceDep = None,
    publisher: EventPublisherDep = None,
    ctx: RequestContextDep = None,
    auth: ClientAuthDep = None,
    platform: PlatformContextDep = None,
    logger: LoggerDep = None
):
    """
    Create product recommendations based on seasonal color analysis.
    
    Requires either shopper_id or anonymous_id for identification.
    Calls Season Compatibility Service to get matching products.
    Emits credit consumption event.
    """
    
    # Validate shop context
    validate_shop_context(
        client_auth=auth,
        platform_ctx=platform,
        logger=logger,
        expected_scope="recommendations:write"
    )
    
    # Extract merchant ID from JWT
    merchant_id = UUID(auth.shop)
    
    try:
        # Create recommendation
        response = await svc.create_recommendation(
            merchant_id=merchant_id,
            platform_name=platform.platform,
            platform_domain=platform.domain,
            request=request,
            correlation_id=ctx.correlation_id
        )
        
        # Emit success event for credit consumption
        await publisher.match_completed(
            MatchCompletedPayload(
                merchant_id=merchant_id,
                match_id=response.match_id,
                shopper_id=request.shopper_id,
                anonymous_id=request.anonymous_id,
                matches_count=response.total_matches,
                primary_season=request.primary_season,
                correlation_id=ctx.correlation_id
            ),
            correlation_id=ctx.correlation_id
        )
        
        return success_response(
            data=response,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id
        )
        
    except Exception as e:
        # Emit failure event for analytics
        await publisher.match_failed(
            MatchFailedPayload(
                merchant_id=merchant_id,
                error_code=getattr(e, 'code', 'UNKNOWN_ERROR'),
                reason=str(e),
                correlation_id=ctx.correlation_id,
                analysis_id=request.analysis_id
            ),
            correlation_id=ctx.correlation_id
        )
        raise  # Let middleware handle error response


@router.get(
    "/{match_id}",
    response_model=ApiResponse[MatchOut],
    summary="Get match details"
)
async def get_match(
    match_id: str,
    svc: RecommendationServiceDep = None,
    ctx: RequestContextDep = None,
    auth: ClientAuthDep = None,
    platform: PlatformContextDep = None,
    logger: LoggerDep = None
):
    """Get match details by ID"""
    
    # Validate shop context
    validate_shop_context(
        client_auth=auth,
        platform_ctx=platform,
        logger=logger,
        expected_scope="recommendations:read"
    )
    
    # Get match - service raises NotFoundError if missing
    match = await svc.get_match(match_id)
    
    # Verify merchant owns this match
    if str(match.merchant_id) != auth.shop:
        raise ValidationError(
            message="Match does not belong to this merchant",
            field="match_id",
            value=match_id
        )
    
    return success_response(
        data=match,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )