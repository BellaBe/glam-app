"""Credit account API endpoints."""

from uuid import UUID
from typing import List
from fastapi import APIRouter, HTTPException, status

from shared.api import (
    ApiResponse,
    success_response,
    RequestContextDep,
)

from ...dependencies import CreditServiceDep
from ...schemas.credit import CreditResponse

router = APIRouter(prefix="", tags=["credits"])


@router.get("/{merchant_id}", 
            response_model=ApiResponse[CreditResponse], 
            summary="Get credits status for merchant",
            status_code=status.HTTP_200_OK
            )
async def get_credit(
    merchant_id: UUID,
    svc: CreditServiceDep,
    ctx: RequestContextDep  
):
    """Get credit account for merchant"""
    credit = await svc.get_credit(merchant_id)
    if not credit:
        raise HTTPException(
            status_code=404,
            detail=f"Credit account not found for merchant {merchant_id}"
        )
    return success_response(
        data=credit,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )

@router.get("admin/zero-balance", 
            response_model=ApiResponse[List[CreditResponse]], 
            summary="Get all merchants with zero balance",
            status_code=status.HTTP_200_OK
            )
async def get_merchants_with_zero_balance(
    svc: CreditServiceDep,
    ctx: RequestContextDep
):
    """Get all merchants with zero balance"""
    merchants = await svc.get_merchants_with_zero_balance()
    return success_response(
        data=merchants,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )
