# glam-app/services/billing-service/src/api/v1/subscriptions.py
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query, Body, status

from shared.api import ApiResponse, success_response, RequestContextDep
from ...dependencies import BillingServiceDep
from ...schemas import (
    SubscriptionCreateIn,
    SubscriptionCreateOut,
    SubscriptionOut,
)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.post(
    "",
    response_model=ApiResponse[SubscriptionCreateOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subscription (initiates Shopify charge)",
)
async def create_subscription(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    body: SubscriptionCreateIn = Body(...),
):
    result = await svc.create_subscription(
        merchant_id=body.merchant_id,
        shop_id=body.shop_id,
        plan_id=body.plan_id,
        return_url=body.return_url,
        test_mode=body.test_mode,
        correlation_id=ctx.correlation_id,
    )

    return success_response(
        data=result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )

@router.get(
    "/{subscription_id}",
    response_model=ApiResponse[SubscriptionOut],
    summary="Get subscription details",
    status_code=status.HTTP_200_OK,
)
async def get_subscription(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    subscription_id: UUID = Path(...),
    
):
    subscription = await svc.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return success_response(
        data=subscription,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )

@router.get(
    "/merchant/{merchant_id}",
    response_model=ApiResponse[List[SubscriptionOut]],
    summary="List a merchant’s subscriptions",
)
async def list_merchant_subscriptions(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(..., description="The ID of the merchant"),
):
    subs = await svc.list_merchant_subscriptions(merchant_id)
    return success_response(
        data=subs,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )

@router.delete(
    "/{subscription_id}",
    response_model=ApiResponse[dict],
    summary="Cancel a subscription",
)
async def cancel_subscription(
    svc: BillingServiceDep,
    ctx: RequestContextDep,
    subscription_id: UUID = Path(...),
    immediate: bool = Query(False),
    reason: str = Query("merchant_request"),

):
    # TODO: use `immediate` / `reason` once business rules are defined
    await svc.cancel_subscription(subscription_id)

    return success_response(
        data={"message": "Subscription cancelled successfully"},
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )
