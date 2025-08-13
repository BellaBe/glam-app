# services/merchant-service/src/api/v1/merchants.py
from fastapi import APIRouter, status, HTTPException
from shared.api import ApiResponse, success_response
from shared.api.dependencies import (
    RequestContextDep, 
    ClientAuthDep, 
    PlatformContextDep,
    LoggerDep
)
from ...dependencies import MerchantServiceDep
from ...schemas import MerchantSyncIn, MerchantSyncOut, MerchantSelfOut
from ...exceptions import MerchantNotFoundError

merchants_router = APIRouter(prefix="/merchants", tags=["merchants"])

@merchants_router.post(
    "/sync",
    response_model=ApiResponse[MerchantSyncOut],
    status_code=status.HTTP_200_OK,
    summary="Sync merchant from OAuth flow",
    description="Create or update merchant after OAuth completion. Used in afterAuth hooks."
)
async def sync_merchant(
    body: MerchantSyncIn,
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    client_auth: ClientAuthDep,
    platform_ctx: PlatformContextDep,
    logger: LoggerDep,  # ✅ Logger automatically has request context
):
    """Sync merchant after OAuth completion."""
    
    # Security validations
    if client_auth.shop != platform_ctx.domain:
        logger.warning(
            "Shop domain mismatch between JWT and headers",
            extra={
                "jwt_shop": client_auth.shop,
                "header_domain": platform_ctx.domain
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "SHOP_DOMAIN_MISMATCH",
                "message": "Shop domain mismatch between JWT and headers",
                "details": {
                    "jwt_shop": client_auth.shop,
                    "header_domain": platform_ctx.domain
                }
            }
        )
    
    if body.platform_domain.lower() != platform_ctx.domain.lower():
        logger.warning(
            "Domain mismatch between request body and header",
            extra={
                "body_domain": body.platform_domain,
                "header_domain": platform_ctx.domain
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "BODY_DOMAIN_MISMATCH", 
                "message": "Shop domain mismatch between request body and header",
                "details": {
                    "body_domain": body.platform_domain,
                    "header_domain": platform_ctx.domain
                }
            }
        )
    
    if body.platform_name.lower() != platform_ctx.platform.lower():
        logger.warning(
            "Platform mismatch between request body and header",
            extra={
                "body_platform": body.platform_name,
                "header_platform": platform_ctx.platform
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "PLATFORM_MISMATCH",
                "message": "Platform mismatch between request body and header", 
                "details": {
                    "body_platform": body.platform_name,
                    "header_platform": platform_ctx.platform
                }
            }
        )
    
    logger.set_request_context(
        platform=platform_ctx.platform,
        domain=platform_ctx.domain,
        platform_id=body.platform_id
    )
    
    logger.info("Starting merchant sync")
    
    try:
        result = await service.sync_merchant(body, ctx)
        
        logger.info(
            "Merchant synced successfully",
            extra={
                "merchant_id": result.merchant_id,
                "operation": "create" if result.created else "update"
            }
        )
        
        return success_response(
            result,
            ctx.request_id,
            ctx.correlation_id
        )
        
    except Exception as e:
        logger.error(
            "Merchant sync failed",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise

@merchants_router.get(
    "/self",
    response_model=ApiResponse[MerchantSelfOut],
    status_code=status.HTTP_200_OK,
    summary="Get current merchant",
    description="Get current merchant using platform context from headers"
)
async def get_current_merchant(
    service: MerchantServiceDep,
    ctx: RequestContextDep,
    client_auth: ClientAuthDep,
    platform_ctx: PlatformContextDep,
    logger: LoggerDep,
):
    """Get current merchant using platform context from headers."""
    
    # Security validation
    if client_auth.shop != platform_ctx.domain:
        logger.warning(
            "Shop domain mismatch between JWT and headers",
            extra={
                "jwt_shop": client_auth.shop,
                "header_domain": platform_ctx.domain
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "SHOP_DOMAIN_MISMATCH",
                "message": "Shop domain mismatch between JWT and headers",
                "details": {
                    "jwt_shop": client_auth.shop,
                    "header_domain": platform_ctx.domain
                }
            }
        )
    
    logger.set_request_context(
        platform=platform_ctx.platform,
        domain=platform_ctx.domain
    )
    
    logger.info("Getting current merchant")
    
    try:
        merchant = await service.get_merchant_by_domain(
            platform_domain=platform_ctx.domain,
        )
        
        logger.info(
            "Current merchant retrieved successfully",
            extra={"merchant_id": merchant.id}
        )
        
        return success_response(
            merchant,
            ctx.request_id,
            ctx.correlation_id
        )
        
    except MerchantNotFoundError:
        logger.warning("Current merchant not found")
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "MERCHANT_NOT_FOUND",
                "message": "Merchant not found for current shop",
                "details": {
                    "platform": platform_ctx.platform,
                    "domain": platform_ctx.domain
                }
            }
        )