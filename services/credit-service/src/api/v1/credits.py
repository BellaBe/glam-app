from fastapi import APIRouter, status, Path
from uuid import UUID
from shared.api import ApiResponse, success_response
from shared.api.dependencies import ClientAuthDep, RequestContextDep
from shared.utils.exceptions import ForbiddenError
from ...dependencies import CreditServiceDep
from ...schemas.credit import CreditBalanceOut

router = APIRouter(prefix="/credits", tags=["Credits"])


@router.get("/{merchant_id}", response_model=ApiResponse[CreditBalanceOut])
async def get_credits(
    merchant_id: UUID = Path(..., description="Merchant ID to fetch credits for"),
    service: CreditServiceDep = None,
    ctx: RequestContextDep = None,
    auth: ClientAuthDep = None
):
    """Get credit balance for merchant"""
    if auth.scope not in ["bff:api:access"]:
        raise ForbiddenError(message="Cannot read credits", required_permission="bff:api:access")
    
    result = await service.get_balance(merchant_id)
    return success_response(result, ctx.correlation_id)
