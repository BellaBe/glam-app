# services/season-compatibility/src/api/v1/compatibility.py
from fastapi import APIRouter, Query, Request

from shared.api import ApiResponse, success_response
from shared.api.dependencies import RequestContextDep
from shared.utils.exceptions import ForbiddenError, UnauthorizedError

from ...dependencies import CompatibilityServiceDep, ConfigDep
from ...schemas.compatibility import CompatibleItemsResponse, SeasonCompatibilityOut, SeasonListResponse
from ...season_palettes import SEASON_PALETTES

router = APIRouter(prefix="/api/v1/compatibility", tags=["Compatibility"])


def validate_internal_auth(request: Request, config: ConfigDep) -> str:
    """Validate internal service authentication"""
    if not config.auth_enabled:
        return "recommendation-service"  # Skip in dev

    api_key = request.headers.get("X-Internal-API-Key")
    service_name = request.headers.get("X-Service-Name")

    if not api_key or not service_name:
        raise UnauthorizedError("Missing authentication headers")

    # Validate API key
    if api_key != config.recommendation_service_api_key:
        raise UnauthorizedError("Invalid API key")

    # Only recommendation-service allowed
    if service_name != "recommendation-service":
        raise ForbiddenError(
            "Only recommendation-service can access this endpoint", required_permission="season-compatibility:read"
        )

    return service_name


@router.get("/items", response_model=ApiResponse[CompatibleItemsResponse], summary="Query compatible items")
async def get_compatible_items(
    request: Request,
    ctx: RequestContextDep,
    config: ConfigDep,
    svc: CompatibilityServiceDep,
    merchant_id: str = Query(..., description="Merchant identifier"),
    seasons: str = Query(..., description="Comma-separated season names"),
    min_score: float = Query(0.7, ge=0.0, le=1.0, description="Minimum score threshold"),
    limit: int = Query(100, ge=1, le=100, description="Max items to return"),
):
    """Get items compatible with given seasons (recommendation-service only)"""
    # Validate auth
    validate_internal_auth(request, config)

    # Parse seasons
    season_list = [s.strip() for s in seasons.split(",")]

    # Get compatible items
    items = await svc.get_compatible_items(
        merchant_id=merchant_id, seasons=season_list, min_score=min_score, limit=limit
    )

    response_data = CompatibleItemsResponse(items=items, total=len(items))

    return success_response(data=response_data, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@router.get("/item/{item_id}", response_model=ApiResponse[SeasonCompatibilityOut], summary="Get single item scores")
async def get_item_scores(
    item_id: str, request: Request, ctx: RequestContextDep, config: ConfigDep, svc: CompatibilityServiceDep
):
    """Get all season scores for a single item"""
    # Validate auth
    validate_internal_auth(request, config)

    # Get item scores
    scores = await svc.get_item_scores(item_id)

    return success_response(data=scores, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@router.get("/seasons", response_model=ApiResponse[SeasonListResponse], summary="Get available seasons")
async def get_available_seasons(request: Request, ctx: RequestContextDep, config: ConfigDep):
    """Get list of available seasons"""
    # Validate auth
    validate_internal_auth(request, config)

    seasons = list(SEASON_PALETTES.keys())

    response_data = SeasonListResponse(seasons=seasons, total=len(seasons))

    return success_response(data=response_data, request_id=ctx.request_id, correlation_id=ctx.correlation_id)
