from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, status, Header

from shared.api import ApiResponse, success_response
from shared.api.dependencies import ClientAuthDep, RequestContextDep
from shared.utils.exceptions import ForbiddenError


billing_router = APIRouter(prefix="/billing")


@billing_router.post(
    "/trial",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Activate trial",
    description="Activate trial credits for merchant",
)
async def activate_trial(
    service,  # BillingServiceDep
    ctx: RequestContextDep,
    auth: ClientAuthDep,
):
    """Activate trial"""
    
    await service.activate_trial(auth.merchant_id, ctx.correlation_id)
    return success_response({"success": True}, ctx.correlation_id)


@billing_router.get(
    "/trial",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Get trial status",
    description="Get trial eligibility and activation status",
)
async def get_trial_status(
    service,  # BillingServiceDep
    ctx: RequestContextDep,
    auth: ClientAuthDep,
):
    """Get trial status"""
    
    result = await service.get_trial_status(auth.merchant_id)
    return success_response(result, ctx.correlation_id)


@billing_router.get(
    "/products",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="List products",
    description="List active pricing products",
)
async def list_products(
    service,  # BillingServiceDep
    ctx: RequestContextDep,
):
    """List pricing products"""
    result = await service.list_products()
    return success_response({"products": result}, ctx.correlation_id)


@billing_router.post(
    "/charges",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create charge",
    description="Create payment charge for credit purchase",
)
async def create_charge(
    data,  # CreateChargeIn
    service,  # BillingServiceDep
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    x_shop_domain: str = Header(...),
):
    """Create charge"""
    
    if auth.shop_domain != x_shop_domain:
        raise ForbiddenError(
            message="Shop domain mismatch",
            required_permission="shop_access"
        )
    
    result = await service.create_charge(
        merchant_id=auth.merchant_id,
        data=data,
        correlation_id=ctx.correlation_id,
    )
    return success_response(result, ctx.correlation_id)


@billing_router.get(
    "/payments",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="List payments",
    description="List payment history for merchant",
)
async def list_payments(
    service,  # BillingServiceDep
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    x_shop_domain: str = Header(...),
    limit: int = 100,
    offset: int = 0,
):
    """List payments"""
    
    if auth.shop_domain != x_shop_domain:
        raise ForbiddenError(
            message="Shop domain mismatch",
            required_permission="shop_access"
        )
    
    result = await service.list_payments(
        merchant_id=auth.merchant_id,
        limit=limit,
        offset=offset,
    )
    return success_response(result, ctx.correlation_id)


@billing_router.get(
    "/payments/{payment_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Get payment",
    description="Get payment details by ID",
)
async def get_payment(
    payment_id: str,
    service,  # BillingServiceDep
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    x_shop_domain: str = Header(...),
):
    """Get payment by ID"""
    
    if auth.shop_domain != x_shop_domain:
        raise ForbiddenError(
            message="Shop domain mismatch",
            required_permission="shop_access"
        )
    
    result = await service.get_payment(payment_id)
    
    # Verify merchant owns this payment
    if result.merchant_id != UUID(auth.merchant_id):
        raise ForbiddenError(
            message="Cannot access payment",
            required_permission="payment_owner"
        )
    
    return success_response(result, ctx.correlation_id)