# services/merchant-service/src/api/v1/merchants.py
from fastapi import APIRouter, HTTPException, status

from shared.api import ApiResponse, success_response
from shared.api.dependencies import (
    ClientAuthDep,
    LoggerDep,
    RequestContextDep,
)

from ...dependencies import MerchantServiceDep
from ...exceptions import MerchantNotFoundError
from ...schemas import MerchantSelfOut, MerchantSyncIn, MerchantSyncOut

merchants_router = APIRouter(prefix="/merchants")


@merchants_router.post(
    "/sync",
    response_model=ApiResponse[MerchantSyncOut],
    status_code=status.HTTP_200_OK,
    summary="Sync merchant from OAuth flow",
    description="Create or update merchant after OAuth completion. Used in afterAuth hooks.",
)
async def sync_merchant(
    body: MerchantSyncIn,
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    client_auth: ClientAuthDep,
    logger: LoggerDep,
):
    """Sync merchant after OAuth completion."""

    if client_auth.domain != body.domain:
        logger.warning(
            "Domain mismatch",
            extra={"client_auth_domain": client_auth.domain, "body_domain": body.domain},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DOMAIN_MISMATCH", "message": "Domain mismatch"},
        )

    logger.set_request_context(
        platform=ctx.platform,
        domain=ctx.domain,
    )

    logger.info("Starting merchant sync")

    try:
        result = await service.sync_merchant(body, ctx)

        logger.info(
            "Merchant synced successfully",
            extra={
                "merchant_id": result.merchant_id,
                "operation": "create" if result.created else "update",
            },
        )

        return success_response(result, ctx.request_id, ctx.correlation_id)

    except Exception as e:
        logger.exception(
            "Merchant sync failed",
            extra={"error_type": type(e).__name__, "error_message": str(e)},
        )
        raise


@merchants_router.get(
    "/self",
    response_model=ApiResponse[MerchantSelfOut],
    status_code=status.HTTP_200_OK,
    summary="Get current merchant",
    description="Get current merchant using platform context from headers",
)
async def get_current_merchant(
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    client_auth: ClientAuthDep,
    logger: LoggerDep,
):
    """Get current merchant using platform context from headers."""
    logger.set_request_context(
        platform=ctx.platform,
        domain=ctx.domain,
    )

    # TODO: verify client_auth

    logger.info("Getting current merchant")

    try:
        merchant = await service.get_merchant_by_domain(
            domain=ctx.domain,
        )

        logger.info(
            "Current merchant retrieved successfully",
            extra={"merchant_id": merchant.id},
        )

        return success_response(merchant, ctx.request_id, ctx.correlation_id)

    except MerchantNotFoundError:
        logger.warning("Current merchant not found")

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "MERCHANT_NOT_FOUND",
                "message": "Merchant not found for current shop",
                "details": {
                    "platform": ctx.platform,
                    "domain": ctx.domain,
                },
            },
        ) from MerchantNotFoundError(f"Merchant not found for domain {ctx.domain}")
