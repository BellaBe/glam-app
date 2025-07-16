# services/webhook-service/src/api/v1/webhooks.py
"""Webhook endpoints for receiving external webhooks."""

import json
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, Body, status
from fastapi.responses import JSONResponse

from shared.api.dependencies import RequestIdDep
from shared.utils.logger import ServiceLogger

from ...dependencies import (
    LifecycleDep,
    ConfigDep,
    WebhookServiceDep,
    PlatformHandlerServiceDep
)
from ...schemas.webhook import WebhookResponse
from ...exceptions import (
    InvalidSignatureError,
    WebhookValidationError,
    PayloadTooLargeError
)

router = APIRouter(tags=["Webhooks"])


@router.post("/shopify/{topic}")
async def receive_shopify_webhook_with_topic(
    topic: str,
    request: Request,
    request_id: RequestIdDep,
    config: ConfigDep,
    webhook_service: WebhookServiceDep,
    platform_handler_service: PlatformHandlerServiceDep,
    x_shopify_topic: str = Header(..., alias="X-Shopify-Topic"),
    x_shopify_hmac_sha256: str = Header(..., alias="X-Shopify-Hmac-Sha256"),
    x_shopify_shop_domain: str = Header(..., alias="X-Shopify-Shop-Domain"),
    x_shopify_api_version: str = Header(..., alias="X-Shopify-API-Version"),
    x_shopify_webhook_id: str = Header(..., alias="X-Shopify-Webhook-Id"),
) -> WebhookResponse:
    """
    Receive Shopify webhook with topic in URL path.
    
    This endpoint handles Shopify webhooks where the topic is specified
    in the URL path (e.g., /webhooks/shopify/orders/create).
    """
    
    return await _process_shopify_webhook(
        topic=topic,
        request=request,
        request_id=request_id,
        config=config,
        webhook_service=webhook_service,
        platform_handler_service=platform_handler_service,
        headers={
            "X-Shopify-Topic": x_shopify_topic,
            "X-Shopify-Hmac-Sha256": x_shopify_hmac_sha256,
            "X-Shopify-Shop-Domain": x_shopify_shop_domain,
            "X-Shopify-API-Version": x_shopify_api_version,
            "X-Shopify-Webhook-Id": x_shopify_webhook_id,
        }
    )


@router.post("/shopify")
async def receive_shopify_webhook_generic(
    request: Request,
    request_id: RequestIdDep,
    config: ConfigDep,
    webhook_service: WebhookServiceDep,
    platform_handler_service: PlatformHandlerServiceDep,
    x_shopify_topic: str = Header(..., alias="X-Shopify-Topic"),
    x_shopify_hmac_sha256: str = Header(..., alias="X-Shopify-Hmac-Sha256"),
    x_shopify_shop_domain: str = Header(..., alias="X-Shopify-Shop-Domain"),
    x_shopify_api_version: str = Header(..., alias="X-Shopify-API-Version"),
    x_shopify_webhook_id: str = Header(..., alias="X-Shopify-Webhook-Id"),
) -> WebhookResponse:
    """
    Receive Shopify webhook with topic in header.
    
    This endpoint handles Shopify webhooks where the topic is specified
    in the X-Shopify-Topic header.
    """
    
    return await _process_shopify_webhook(
        topic=x_shopify_topic,
        request=request,
        request_id=request_id,
        config=config,
        webhook_service=webhook_service,
        platform_handler_service=platform_handler_service,
        headers={
            "X-Shopify-Topic": x_shopify_topic,
            "X-Shopify-Hmac-Sha256": x_shopify_hmac_sha256,
            "X-Shopify-Shop-Domain": x_shopify_shop_domain,
            "X-Shopify-API-Version": x_shopify_api_version,
            "X-Shopify-Webhook-Id": x_shopify_webhook_id,
        }
    )


async def _process_shopify_webhook(
    topic: str,
    request: Request,
    request_id: str,
    config: Any,
    webhook_service: Any,
    platform_handler_service: Any,
    headers: Dict[str, str]
) -> WebhookResponse:
    """Internal function to process Shopify webhooks."""
    
    logger = ServiceLogger(config.service_name)
    
    try:
        # Read raw body
        body = await request.body()
        
        # Check payload size
        if len(body) > config.webhook_max_payload_size_mb * 1024 * 1024:
            raise PayloadTooLargeError(
                f"Payload size {len(body)} exceeds maximum {config.webhook_max_payload_size_mb}MB"
            )
        
        # Validate signature
        if not platform_handler_service.validate_webhook("shopify", body, headers):
            logger.warning(
                "Invalid webhook signature",
                extra={
                    "platform": "shopify",
                    "topic": topic,
                    "request_id": request_id,
                    "shop_domain": headers.get("X-Shopify-Shop-Domain")
                }
            )
            raise InvalidSignatureError("Invalid webhook signature")
        
        # Parse JSON payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(
                "Failed to parse webhook payload",
                extra={
                    "platform": "shopify",
                    "topic": topic,
                    "request_id": request_id,
                    "error": str(e)
                }
            )
            raise WebhookValidationError(f"Invalid JSON payload: {str(e)}")
        
        # Process webhook
        webhook_entry = await webhook_service.process_webhook(
            platform="shopify",
            topic=topic,
            payload=payload,
            headers=headers,
            signature=headers["X-Shopify-Hmac-Sha256"]
        )
        
        logger.info(
            "Webhook processed successfully",
            extra={
                "platform": "shopify",
                "topic": topic,
                "request_id": request_id,
                "webhook_id": str(webhook_entry.id),
                "shop_domain": headers.get("X-Shopify-Shop-Domain")
            }
        )
        
        return WebhookResponse(
            success=True,
            webhook_id=webhook_entry.id,
            message="Webhook processed successfully"
        )
        
    except (InvalidSignatureError, WebhookValidationError, PayloadTooLargeError):
        # Re-raise known webhook errors
        raise
    
    except Exception as e:
        logger.error(
            "Unexpected error processing webhook",
            extra={
                "platform": "shopify",
                "topic": topic,
                "request_id": request_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        # Return 200 OK even for processing errors to prevent retries
        # The webhook entry will be marked as failed in the database
        return WebhookResponse(
            success=False,
            webhook_id="00000000-0000-0000-0000-000000000000",  # Placeholder UUID
            message=f"Webhook processing failed: {str(e)}"
        )
