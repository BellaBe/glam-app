# services/token-service/src/api/v1/tokens.py


from fastapi import APIRouter, Body, status

from shared.api import ApiResponse, success_response
from shared.api.dependencies import ClientAuthDep, InternalAuthDep, RequestContextDep
from shared.api.validation import ensure_allowed_service
from shared.utils.exceptions import UnauthorizedError

from ...dependencies import LoggerDep, TokenServiceDep
from ...schemas.token import DeleteTokenResponse, StoreTokenRequest, StoreTokenResponse, TokenListResponse

router = APIRouter(prefix="/api/v1/tokens", tags=["Tokens"])


@router.post(
    "",
    response_model=ApiResponse[StoreTokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Store or update token",
)
async def store_token(
    svc: TokenServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    logger: LoggerDep,
    body: StoreTokenRequest = Body(...),
):
    """
    Store or update platform token (requires client auth).
    Used by BFF after OAuth callback.
    """

    # Validate domain matches JWT
    if body.domain != auth.shop:
        logger.warning(
            "Domain mismatch",
            extra={"jwt_domain": auth.shop, "request_domain": body.domain},
        )
        raise UnauthorizedError("Domain mismatch", details={"jwt_domain": auth.shop, "request_domain": body.domain})

    # Store token
    token_id = await svc.store_token(request=body, correlation_id=ctx.correlation_id)

    return success_response(
        data=StoreTokenResponse(token_id=token_id, status="stored"),
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )


@router.get("/{merchant_id}", response_model=ApiResponse[TokenListResponse], summary="Get tokens for merchant")
async def get_tokens(
    merchant_id: str,
    svc: TokenServiceDep,
    ctx: RequestContextDep,
    auth: InternalAuthDep,
    logger: LoggerDep,
):
    """
    Retrieve tokens for a merchant (requires internal auth).
    Used by Platform Connector and other internal services.
    """

    # Validate service is allowed to retrieve tokens
    ensure_allowed_service(auth, ["billing-svc", "catalog-svc"], operation="get-token", logger=logger)

    # Get tokens
    tokens = await svc.get_tokens(
        merchant_id=merchant_id,
        platform=ctx.platform,
        requesting_service=auth.service,
        correlation_id=ctx.correlation_id,
        ip_address=ctx.ip_client,
    )

    return success_response(
        data=TokenListResponse(tokens=tokens), request_id=ctx.request_id, correlation_id=ctx.correlation_id
    )


@router.delete(
    "/{merchant_id}/{platform}", response_model=ApiResponse[DeleteTokenResponse], summary="Delete specific token"
)
async def delete_token(
    merchant_id: str,
    platform: str,
    svc: TokenServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    logger: LoggerDep,
):
    """
    Delete a specific token (requires client auth).
    Used when merchant disconnects a platform.
    """

    # In production, verify merchant ownership
    # For now, just ensure JWT is valid
    if not auth.shop:
        raise UnauthorizedError("Invalid authentication")

    # Delete token
    deleted = await svc.delete_token(merchant_id=merchant_id, platform=platform, correlation_id=ctx.correlation_id)

    if not deleted:
        logger.warning("Token not found for deletion", extra={"merchant_id": merchant_id, "platform": platform})

    return success_response(
        data=DeleteTokenResponse(status="deleted"), request_id=ctx.request_id, correlation_id=ctx.correlation_id
    )
