from fastapi import APIRouter, status, HTTPException, Header, Request
from typing import Optional
from shared.api import ApiResponse, success_response, error_response
from shared.api.dependencies import RequestContextDep, ClientIpDep, AuthDep, ShopDomainDep
from ...dependencies import MerchantServiceDep
from ...schemas.merchant import (
    MerchantSync, MerchantOut, MerchantSettingsUpdate,
    MerchantSettingsOut, MerchantSyncOut, MerchantActivity
)
from ...exceptions import (
    MerchantNotFoundError, InvalidDomainError,
    InvalidStatusTransitionError, ConsentViolationError
)

router = APIRouter()

@router.post(
    "/sync",
    response_model=ApiResponse[MerchantSyncOut],
    status_code=status.HTTP_200_OK,
    summary="Sync merchant from OAuth flow",
)
async def sync_merchant(
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    shop_domain_header: ShopDomainDep,
    body: MerchantSync,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Sync merchant after OAuth completion"""
    try:
        # Validate shop domain matches header
        if body.shop_domain.lower() != shop_domain_header:
            raise InvalidDomainError("Shop domain mismatch between body and header")
        
        result = await service.sync_merchant(body, idempotency_key)
        return success_response(
            result,
            ctx.request_id,
            ctx.correlation_id
        )
    except InvalidDomainError as e:
        return error_response(
            code="INVALID_DOMAIN",
            message=str(e),
            # status=400,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id
        )
    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message="Failed to sync merchant",
            # status=500,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id
        )

@router.get(
    "/self",
    response_model=ApiResponse[MerchantOut],
    summary="Get current merchant info",
)
async def get_merchant_self(
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    auth: AuthDep,
    shop_domain: ShopDomainDep
):
    """Get current merchant information"""
    try:
        merchant = await service.get_merchant_by_domain(shop_domain)
        return success_response(
            merchant,
            ctx.request_id,
            ctx.correlation_id
        )
    except MerchantNotFoundError:
        raise HTTPException(404, "Merchant not found")

@router.get(
    "/self/settings",
    response_model=ApiResponse[MerchantSettingsOut],
    summary="Get current merchant settings",
)
async def get_merchant_settings(
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    auth: AuthDep,
    shop_domain: ShopDomainDep
):
    """Get current merchant settings"""
    try:
        settings = await service.get_settings(shop_domain)
        return success_response(
            settings,
            ctx.request_id,
            ctx.correlation_id
        )
    except MerchantNotFoundError:
        raise HTTPException(404, "Merchant not found")

@router.put(
    "/self/settings",
    response_model=ApiResponse[MerchantSettingsOut],
    summary="Update merchant settings",
)
async def update_merchant_settings(
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    auth: AuthDep,
    shop_domain: ShopDomainDep,
    client_ip: ClientIpDep,
    body: MerchantSettingsUpdate,
    request: Request
):
    """Update merchant settings"""
    try:
        user_agent = request.headers.get("user-agent")
        settings = await service.update_settings(
            shop_domain,
            body,
            ip=client_ip,
            user_agent=user_agent
        )
        return success_response(
            settings,
            ctx.request_id,
            ctx.correlation_id
        )
    except MerchantNotFoundError:
        raise HTTPException(404, "Merchant not found")
    except ConsentViolationError as e:
        return error_response(
            code="CONSENT_VIOLATION",
            message=str(e),
            # status=409,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id
        )

@router.post(
    "/self/activity",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Record merchant activity",
)
async def record_merchant_activity(
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    auth: AuthDep,
    shop_domain: ShopDomainDep,
    body: MerchantActivity
):
    """Record merchant activity for analytics"""
    try:
        await service.record_activity(shop_domain, body)
    except MerchantNotFoundError:
        raise HTTPException(404, "Merchant not found")

