# services/webhook-service/src/api/v1/webhooks.py
"""Webhook API endpoints."""

from fastapi import APIRouter, Request, Response, Header, HTTPException
from typing import Optional, Dict, Any

from shared.api.responses import success_response, error_response
from shared.errors import ValidationError

from ...dependencies import WebhookServiceDep
from ...models.webhook_entry import WebhookSource


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/shopify/{topic}")
async def shopify_webhook_with_topic(
    request: Request,
    topic: str,
    webhook_service: WebhookServiceDep,
    x_shopify_topic: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None),
    x_shopify_webhook_id: Optional[str] = Header(None),
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_api_version: Optional[str] = Header(None)
) -> Response:
    """Handle Shopify webhook with topic in path"""
    
    # Validate required headers
    if not x_shopify_hmac_sha256:
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    if not x_shopify_shop_domain:
        raise HTTPException(status_code=400, detail="Missing shop domain header")
    
    # Get raw body
    body = await request.body()
    
    # Build headers dict
    headers = {
        "x-shopify-topic": x_shopify_topic or topic,
        "x-shopify-shop-domain": x_shopify_shop_domain,
        "x-shopify-webhook-id": x_shopify_webhook_id,
        "x-shopify-hmac-sha256": x_shopify_hmac_sha256,
        "x-shopify-api-version": x_shopify_api_version
    }
    
    try:
        result = await webhook_service.process_webhook(
            source=WebhookSource.SHOPIFY,
            headers=headers,
            body=body,
            topic=topic
        )
        
        # Always return 200 for accepted webhooks
        return Response(status_code=200)
        
    except ValidationError as e:
        # Return 401 for auth failures
        if "signature" in str(e).lower():
            raise HTTPException(status_code=401, detail=str(e))
        # Return 400 for other validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log but return 200 to prevent retries
        return Response(status_code=200)


@router.post("/shopify")
async def shopify_webhook_fallback(
    request: Request,
    webhook_service: WebhookServiceDep,
    x_shopify_topic: str = Header(...),
    x_shopify_shop_domain: str = Header(...),
    x_shopify_webhook_id: Optional[str] = Header(None),
    x_shopify_hmac_sha256: str = Header(...),
    x_shopify_api_version: Optional[str] = Header(None)
) -> Response:
    """Handle Shopify webhook with topic in header (fallback)"""
    
    body = await request.body()
    
    headers = {
        "x-shopify-topic": x_shopify_topic,
        "x-shopify-shop-domain": x_shopify_shop_domain,
        "x-shopify-webhook-id": x_shopify_webhook_id,
        "x-shopify-hmac-sha256": x_shopify_hmac_sha256,
        "x-shopify-api-version": x_shopify_api_version
    }
    
    try:
        result = await webhook_service.process_webhook(
            source=WebhookSource.SHOPIFY,
            headers=headers,
            body=body,
            topic=x_shopify_topic
        )
        
        return Response(status_code=200)
        
    except ValidationError as e:
        if "signature" in str(e).lower():
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        return Response(status_code=200)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    webhook_service: WebhookServiceDep,
    stripe_signature: str = Header(...)
) -> Response:
    """Handle Stripe webhook"""
    
    body = await request.body()
    
    headers = {
        "stripe-signature": stripe_signature
    }
    
    try:
        # Parse body to get event type
        import json
        parsed = json.loads(body)
        topic = parsed.get("type", "unknown")
        
        result = await webhook_service.process_webhook(
            source=WebhookSource.STRIPE,
            headers=headers,
            body=body,
            topic=topic
        )
        
        return Response(status_code=200)
        
    except ValidationError as e:
        if "signature" in str(e).lower():
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        return Response(status_code=200)


@router.post("/{source}")
async def generic_webhook(
    request: Request,
    source: str,
    webhook_service: WebhookServiceDep
) -> Response:
    """Handle generic webhook (future extensibility)"""
    
    # For now, just accept and log
    body = await request.body()
    headers = dict(request.headers)
    
    # Log for future implementation
    webhook_service.logger.info(
        f"Received webhook from unsupported source: {source}",
        extra={
            "source": source,
            "headers": headers
        }
    )
    
    return Response(status_code=200)