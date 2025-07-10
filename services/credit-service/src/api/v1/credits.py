"""Credit account API endpoints."""

from uuid import UUID
from fastapi import APIRouter

from shared.api.responses import success_response
from shared.api.dependencies import PaginationParams, apply_pagination_params

from ...dependencies import CreditServiceDep
from ...schemas.credit_account import CreditAccountResponse

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/{merchant_id}")
async def get_credit(
    merchant_id: UUID,
    credit_service: CreditServiceDep
) -> CreditAccountResponse:
    """Get credit account for merchant"""
    account = await credit_service.get_account(merchant_id)
    return success_response(account)


@router.get("/{merchant_id}/balance")
async def get_balance(
    merchant_id: UUID,
    credit_service: CreditServiceDep
) -> dict:
    """Get quick balance check for merchant"""
    account = await credit_service.get_account(merchant_id)
    return success_response({
        "merchant_id": str(merchant_id),
        "balance": float(account.balance),
        "last_recharge_at": account.last_recharge_at.isoformat() if account.last_recharge_at else None
    })