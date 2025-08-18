# services/credit-service/src/api/v1/credits.py
from uuid import UUID

from fastapi import APIRouter, Request

from shared.api import ApiResponse, paginated_response, success_response
from shared.api.dependencies import (
    ClientAuthDep,
    PaginationDep,
    PlatformContextDep,
    RequestContextDep,
)
from shared.api.validation import validate_shop_context

from ...dependencies import CreditServiceDep, LoggerDep
from ...schemas.credit import CreditBalanceOut, TransactionListOut

router = APIRouter(prefix="/api", tags=["Credits"])


@router.get(
    "/credits",
    response_model=ApiResponse[CreditBalanceOut],
    summary="Get credit balance",
    description="Get current credit balance with platform context",
)
async def get_credits(
    svc: CreditServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    logger: LoggerDep,
):
    """
    Get credit balance for authenticated merchant.
    Returns balance with platform context.
    """

    # Validate shop context
    validate_shop_context(
        client_auth=auth,
        platform_ctx=platform,
        logger=logger,
        expected_scope="bff:call",  # Only BFF can call
    )

    # Get balance - service raises NotFoundError if missing
    balance = await svc.get_balance(
        merchant_id=UUID(auth.shop),
        platform_domain=platform.domain,
        correlation_id=ctx.correlation_id,
    )

    return success_response(data=balance, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@router.get(
    "/credits/transactions",
    response_model=ApiResponse[list[TransactionListOut]],
    summary="Get transaction history",
    description="Get paginated credit transaction history",
)
async def get_transactions(
    svc: CreditServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    pagination: PaginationDep,
    request: Request,
    logger: LoggerDep,
):
    """
    Get credit transaction history for authenticated merchant.
    Returns paginated list of transactions.
    """

    # Validate shop context
    validate_shop_context(
        client_auth=auth,
        platform_ctx=platform,
        logger=logger,
        expected_scope="bff:call",
    )

    # Get transactions
    total, transactions = await svc.get_transactions(
        merchant_id=UUID(auth.shop),
        page=pagination.page,
        limit=pagination.limit,
        correlation_id=ctx.correlation_id,
    )

    # Return paginated response
    return paginated_response(
        data=transactions,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        base_url=str(request.url.path),
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )
