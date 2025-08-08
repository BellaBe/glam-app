from fastapi import APIRouter, status, HTTPException, Query
from shared.api import ApiResponse, success_response
from shared.api.dependencies import RequestContextDep
from ...dependencies import (
    CreditServiceDep, ShopDomainDep, AdminAuthDep
)
from ...schemas.credit import (
    BalanceOut, CreditGrantIn, CreditGrantOut, LedgerOut
)
from ...exceptions import (
    InvalidDomainError, InvalidAmountError,
    MerchantCreditNotFoundError
)
from ...utils import normalize_shop_domain

router = APIRouter(tags=["credits"])

@router.get(
    "/api/credits/current",
    response_model=ApiResponse[BalanceOut],
    status_code=status.HTTP_200_OK,
    summary="Get current credit balance",
    description="Get the current credit balance for a merchant"
)
async def get_current_balance(
    service: CreditServiceDep,
    ctx: RequestContextDep,
    shop_domain: ShopDomainDep
):
    """Get current credit balance for a merchant"""
    try:
        balance = await service.get_balance(shop_domain)
        return success_response(
            balance,
            ctx.request_id,
            ctx.correlation_id
        )
    except InvalidDomainError:
        raise HTTPException(400, "Invalid shop domain format")
    except Exception as e:
        raise HTTPException(500, "Failed to retrieve balance")

@router.post(
    "/internal/credits/grant",
    response_model=ApiResponse[CreditGrantOut],
    status_code=status.HTTP_200_OK,
    summary="Grant credits (admin)",
    description="Grant credits to a merchant (admin endpoint)"
)
async def grant_credits(
    service: CreditServiceDep,
    ctx: RequestContextDep,
    grant: CreditGrantIn,
    _auth: AdminAuthDep
):
    """Grant credits to a merchant (admin only)"""
    try:
        result = await service.grant_credits(grant, ctx)
        return success_response(
            result,
            ctx.request_id,
            ctx.correlation_id
        )
    except InvalidDomainError as e:
        raise HTTPException(400, str(e))
    except InvalidAmountError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, "Failed to grant credits")

@router.get(
    "/internal/credits/ledger/{shop_domain}",
    response_model=ApiResponse[LedgerOut],
    status_code=status.HTTP_200_OK,
    summary="Get credit ledger (admin)",
    description="Get credit ledger entries for a merchant (admin endpoint)"
)
async def get_credit_ledger(
    service: CreditServiceDep,
    ctx: RequestContextDep,
    shop_domain: str,
    _auth: AdminAuthDep,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get credit ledger for audit trail (admin only)"""
    try:
        # Normalize domain
        shop_domain = normalize_shop_domain(shop_domain)
        
        ledger = await service.get_ledger(shop_domain)
        return success_response(
            ledger,
            ctx.request_id,
            ctx.correlation_id
        )
    except InvalidDomainError:
        raise HTTPException(400, "Invalid shop domain format")
    except Exception as e:
        raise HTTPException(500, "Failed to retrieve ledger")

