"""Router layer – I/O only, zero business logic."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from ...schemas.merchant import MerchantIn, MerchantOut, MerchantPatch
from ...services.merchant import MerchantService
from ..responses import ApiResponse, success_response  # tiny helper, see shared/api.py
from ...exceptions import MerchantNotFoundError
from ...dependencies import RequestContextDep, merchant_service_dep

router = APIRouter(prefix="/api/v1/merchants", tags=["Merchants"])


@router.get("/{merchant_id}", response_model=ApiResponse[MerchantOut])
async def get_merchant(
    merchant_id: UUID = Path(...),
    svc: MerchantService = Depends(merchant_service_dep),
    ctx: RequestContextDep = Depends(),
):
    try:
        out = await svc.get(merchant_id)
        return success_response(out, ctx.request_id, ctx.correlation_id)
    except MerchantNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Merchant not found")