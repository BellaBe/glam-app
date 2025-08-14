# shared/api/validation.py
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from shared.api.dependencies import ClientAuthContext, PlatformContext
from shared.utils.logger import ServiceLogger


def validate_shop_context(
    client_auth: ClientAuthContext,
    platform_ctx: PlatformContext,
    logger: ServiceLogger,
    body_platform: Optional[str] = None,
    body_domain: Optional[str] = None,
    expected_platform: Optional[str] = None,
    expected_scope: Optional[str] = None,
    webhook_payload: Optional[Dict[str, Any]] = None
) -> None:
    """
    Unified validation for shop context across auth, headers, body, and webhooks.
    
    Args:
        client_auth: JWT authentication context
        platform_ctx: Platform context from headers
        logger: Service logger
        body_platform: Platform from request body (if applicable)
        body_domain: Domain from request body (if applicable)
        expected_platform: Expected platform for this endpoint (e.g., "shopify")
        expected_scope: Expected JWT scope (e.g., "bff:call")
        webhook_payload: Webhook payload for platform-specific validation
    
    Raises:
        HTTPException: On any validation failure
    """
    
    # 1. Validate expected platform (for platform-specific endpoints)
    if expected_platform and platform_ctx.platform != expected_platform:
        logger.warning(
            f"Invalid platform for {expected_platform}-only endpoint",
            extra={
                "received_platform": platform_ctx.platform,
                "expected_platform": expected_platform
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PLATFORM",
                "message": f"This endpoint only accepts {expected_platform} requests",
                "details": {
                    "received": platform_ctx.platform,
                    "expected": expected_platform
                }
            }
        )
    
    # 2. Validate JWT shop matches header domain
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
    
    # 3. Validate JWT scope if specified
    if expected_scope and client_auth.scope != expected_scope:
        logger.warning(
            "Invalid JWT scope",
            extra={
                "received_scope": client_auth.scope,
                "expected_scope": expected_scope
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INVALID_SCOPE",
                "message": f"Invalid JWT scope",
                "details": {
                    "received": client_auth.scope,
                    "expected": expected_scope
                }
            }
        )
    
    # 4. Validate body domain if provided
    if body_domain and body_domain.lower() != platform_ctx.domain.lower():
        logger.warning(
            "Domain mismatch between request body and header",
            extra={
                "body_domain": body_domain,
                "header_domain": platform_ctx.domain
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BODY_DOMAIN_MISMATCH",
                "message": "Domain mismatch between request body and header",
                "details": {
                    "body_domain": body_domain,
                    "header_domain": platform_ctx.domain
                }
            }
        )
    
    # 5. Validate body platform if provided
    if body_platform and body_platform.lower() != platform_ctx.platform.lower():
        logger.warning(
            "Platform mismatch between request body and header",
            extra={
                "body_platform": body_platform,
                "header_platform": platform_ctx.platform
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PLATFORM_MISMATCH",
                "message": "Platform mismatch between request body and header",
                "details": {
                    "body_platform": body_platform,
                    "header_platform": platform_ctx.platform
                }
            }
        )
    
    # 6. Platform-specific webhook payload validation
    if webhook_payload:
        if platform_ctx.is_shopify:
            # Shopify-specific validation
            payload_domain = (
                webhook_payload.get("myshopify_domain") or 
                webhook_payload.get("domain") or 
                ""
            ).lower()
            
            if payload_domain and payload_domain != platform_ctx.domain:
                logger.warning(
                    "Shopify webhook payload domain mismatch",
                    extra={
                        "payload_domain": payload_domain,
                        "header_domain": platform_ctx.domain
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "WEBHOOK_DOMAIN_MISMATCH",
                        "message": "Webhook payload domain doesn't match header domain",
                        "details": {
                            "payload_domain": payload_domain,
                            "header_domain": platform_ctx.domain
                        }
                    }
                )
        
        # Add other platform-specific validations as needed
        # elif platform_ctx.platform == "bigcommerce":
        #     ...

# Usage patterns:

# Minimal validation (just auth consistency)
# validate_shop_context(client_auth, platform_ctx, logger)

# # With body validation
# validate_shop_context(
#     client_auth, platform_ctx, logger,
#     body_platform=body.platform,
#     body_domain=body.domain
# )

# # Platform-specific endpoint
# validate_shop_context(
#     client_auth, platform_ctx, logger,
#     expected_platform="shopify"
# )

# # Webhook with all validations
# validate_shop_context(
#     client_auth, platform_ctx, logger,
#     expected_platform="shopify",
#     expected_scope="bff:call",
#     webhook_payload=payload
# )