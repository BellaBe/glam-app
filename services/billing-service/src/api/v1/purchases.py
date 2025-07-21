# glam-app/services/billing-service/src/api/v1/purchases.py
from typing import List
from fastapi import APIRouter, status

from shared.api import (
    ApiResponse,
    success_response,
    RequestContextDep,
)

from ...schemas import(
    OneTimePurchaseIn, OneTimePurchaseOut
)

from ...dependencies import OneTimePurchaseServiceDep

router = APIRouter(prefix="/purchases", tags=["Purchases"])

@router.post("", 
             response_model=ApiResponse[OneTimePurchaseOut], 
             summary="Create one-time credit purchase",
             status_code=status.HTTP_201_CREATED)
async def create_purchase(data: OneTimePurchaseIn, svc: OneTimePurchaseServiceDep, ctx: RequestContextDep):
    """Create one-time credit purchase"""

    result = await svc.create_purchase(data, ctx=ctx)
    
    return success_response(
        data=result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )


