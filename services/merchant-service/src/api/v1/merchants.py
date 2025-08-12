from fastapi import APIRouter, status, HTTPException, Header, Request
from typing import Optional
from json import JSONDecodeError, loads as json_loads, dumps as json_dumps
import json
from shared.api import ApiResponse, success_response, error_response
from shared.api.dependencies import RequestContextDep, ClientIpDep, AuthDep, ShopDomainDep
from ...dependencies import MerchantServiceDep
from ...schemas.merchant import (
    MerchantSync, MerchantOut, MerchantSettingsUpdate,
    MerchantSettingsOut, MerchantSyncOut, MerchantActivity
)
from ...exceptions import (
    MerchantNotFoundError, 
    InvalidDomainError, 
    ConsentViolationError
    )

merchants_router = APIRouter(prefix="/merchants")

@merchants_router.post(
    "/sync",
    # response_model=ApiResponse[MerchantSyncOut],
    status_code=status.HTTP_200_OK,
    summary="Sync merchant from OAuth flow",
)
async def sync_merchant(
    request: Request,
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    shop_domain_header: ShopDomainDep,
    body: MerchantSync,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Sync merchant after OAuth completion"""
    # Get raw body
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')
    
    print("[SYNC ENDPOINT] ===== RAW REQUEST DATA =====")
    print(f"[SYNC ENDPOINT] Headers: {dict(request.headers)}")
    print(f"[SYNC ENDPOINT] Raw Body String: {body_str}")
    
    # try:
    #     body_json = json.loads(body_str)
    #     print(f"[SYNC ENDPOINT] Parsed JSON: {json.dumps(body_json, indent=2)}")
    #     print(f"[SYNC ENDPOINT] JSON Keys: {list(body_json.keys())}")
        
    #     # Now try to validate with Pydantic manually
    #     try:
    #         merchant_data = MerchantSync(**body_json)
    #         print(f"[SYNC ENDPOINT] ✓ Validation successful: {merchant_data.model_dump_json()}")
    #     except Exception as e:
    #         print(f"[SYNC ENDPOINT] ✗ Validation failed: {e}")
    #         print(f"[SYNC ENDPOINT] Validation errors: {e.errors() if hasattr(e, 'errors') else str(e)}")
    #         raise
            
    # except JSONDecodeError as e:
    #     print(f"[SYNC ENDPOINT] Failed to parse JSON: {e}")
    #     raise
    
    # # Your actual logic here
    # return {"status": "ok"}
    try:
        
        print(f"[SYNC] Successfully validated merchant data: {body.model_dump_json()}")
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

@merchants_router.get(
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

@merchants_router.get(
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

@merchants_router.put(
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

@merchants_router.post(
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

