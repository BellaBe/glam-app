# services/merchant-service/src/api/router.py


# ================================================================
# services/merchant-service/src/api/v1/merchants.py
from uuid import UUID
from fastapi import APIRouter, Path, Body, status, HTTPException, Query
from shared.api import ApiResponse, success_response, RequestContextDep
from ...dependencies import MerchantServiceDep
from ...schemas.merchant import MerchantResponse, MerchantConfigResponse, MerchantConfigUpdate, ActivityRecord
from ...exceptions import MerchantNotFoundError

router = APIRouter(prefix="/merchants", tags=["Merchants"])

@router.get(
    "/{merchant_id}",
    response_model=ApiResponse[MerchantResponse],
    summary="Get Merchant by ID",
)
async def get_merchant(
    svc: MerchantServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
):
    """Get merchant by canonical UUID"""
    try:
        merchant = await svc.get_merchant(merchant_id)
        return success_response(merchant, ctx.request_id, ctx.correlation_id)
    except MerchantNotFoundError:
        raise HTTPException(404, "Merchant not found")

@router.get(
    "/lookup",
    response_model=ApiResponse[MerchantResponse],
    summary="Lookup Merchant by Platform ID",
)
async def lookup_merchant(
    svc: MerchantServiceDep,
    ctx: RequestContextDep,
    platform: str = Query(..., description="Platform name (e.g., 'shopify', 'woocommerce')"),
    external_id: str = Query(..., description="Platform-specific store ID"),
):
    """Lookup merchant by platform-specific external ID"""
    try:
        merchant = await svc.lookup_merchant(platform, external_id)
        return success_response(merchant, ctx.request_id, ctx.correlation_id)
    except MerchantNotFoundError:
        raise HTTPException(404, "Merchant not found")

@router.get(
    "/{merchant_id}/config",
    response_model=ApiResponse[MerchantConfigResponse],
    summary="Get Merchant Configuration",
)
async def get_merchant_config(
    svc: MerchantServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
):
    """Get merchant configuration"""
    try:
        merchant = await svc.get_merchant(merchant_id)
        return success_response(merchant.configuration, ctx.request_id, ctx.correlation_id)
    except MerchantNotFoundError:
        raise HTTPException(404, "Merchant not found")

@router.patch(
    "/{merchant_id}/config",
    response_model=ApiResponse[MerchantConfigResponse],
    summary="Update Merchant Configuration",
)
async def update_merchant_config(
    svc: MerchantServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    config_data: MerchantConfigUpdate = Body(...),
):
    """Update merchant configuration"""
    try:
        updated_config = await svc.update_merchant_configuration(merchant_id, config_data)
        return success_response(updated_config, ctx.request_id, ctx.correlation_id)
    except MerchantNotFoundError:
        raise HTTPException(404, "Merchant not found")

@router.post(
    "/{merchant_id}/activity",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Record Activity",
)
async def record_activity(
    svc: MerchantServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    activity_data: ActivityRecord = Body(...),
):
    """Record merchant activity"""
    await svc.record_activity(merchant_id, activity_data)
    return