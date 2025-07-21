# glam-app/services/billing-service/src/api/v1/plans.py
from typing import List
from fastapi import APIRouter, HTTPException, status, Body, Path

from shared.api import (
    ApiResponse,
    success_response,
    RequestContextDep,
)

from ...dependencies import BillingServiceDep

from ...schemas import ( 
    BillingPlanIn,
    BillingPlanPatch,
    BillingPlanOut,
)


router = APIRouter(prefix="/plans", tags=["Plans"])

@router.get("", 
            response_model=ApiResponse[List[BillingPlanOut]], 
            summary="List all billing plans",
            status_code=status.HTTP_200_OK
            )
async def list_plans(
    svc: BillingServiceDep,
    ctx: RequestContextDep
):
    """List all available billing plans"""
    plans = await svc.get_all_plans()
    return success_response(
        data=plans,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

@router.get("/{plan_id}", 
            response_model=ApiResponse[BillingPlanOut], 
            summary="Get billing plan details",
            status_code=status.HTTP_200_OK
            )

async def get_plan(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    plan_id: str = Path(..., min_length=1, max_length=100)
):
    """Get details of a specific billing plan"""
    plan = await svc.get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return success_response(
        data=plan,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

@router.post(
    "",
    response_model=ApiResponse[BillingPlanOut],
    summary="Create a new billing plan",
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    body: BillingPlanIn = Body(...)
):
    plan = await svc.create_plan(body)
    return success_response(
        data=plan,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )

@router.patch(
    "/{plan_id}",
    response_model=ApiResponse[BillingPlanOut],
    summary="Partially update a billing plan",
    status_code=status.HTTP_200_OK,
)
async def patch_plan(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    plan_id: str = Path(..., min_length=1, max_length=100),
    patch: BillingPlanPatch = Body(...),
):
    plan = await svc.patch_plan(plan_id, patch)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return success_response(
        data=plan,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )
