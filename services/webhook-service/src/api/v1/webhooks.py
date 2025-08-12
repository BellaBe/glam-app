# services/webhook-service/src/api/v1/webhooks.py
from fastapi import APIRouter, Body, HTTPException
import json

from shared.api.dependencies import RequestContextDep, InternalJwtDep, ShopifyHeadersDep
from ...dependencies import WebhookServiceDep
from ...models import WebhookPlatform, parse_topic
from ...exceptions import PayloadTooLargeError, MalformedPayloadError, DomainMismatchError, InvalidContentTypeError
from ...schemas.webhooks import WebhookResponse


router = APIRouter(prefix="/webhooks")

@router.post("/shopify", response_model=WebhookResponse)
async def receive_shopify_webhook(
    svc: WebhookServiceDep,
    ctx: RequestContextDep,
    auth: InternalJwtDep,
    headers: ShopifyHeadersDep,
    body: bytes = Body(...),
) -> WebhookResponse:
    """
    Receive webhook from Shopify BFF.
    """
    
    ct = (ctx.content_type or "").lower()
    if "application/json" not in ct:
        raise InvalidContentTypeError(ct)
    
    
    # Check payload size
    if len(body) > 2097152:  # 2MB limit
        raise PayloadTooLargeError(len(body), 2097152)
    
    # Parse the body
    try:
        payload = json.loads(body)
    except Exception:
        raise MalformedPayloadError()
    
    # Extract headers
    shop_domain = headers.shop_domain
    topic = parse_topic(headers.topic_raw)
    webhook_id = headers.webhook_id
    
    # Validate shop domain matches JWT
    if auth.shop != shop_domain:
        raise DomainMismatchError(
            header_domain=shop_domain,
            jwt_domain=auth.shop
        )
    
    # Validate scope
    if auth.scope != "bff:call":
        raise HTTPException(
            status_code=403,
            detail=f"Invalid JWT scope: {auth.scope}. Expected: bff:call"
        )
    
    payload_domain = (payload.get("myshopify_domain") or payload.get("domain") or "").lower()
    if payload_domain and payload_domain != shop_domain:
        raise DomainMismatchError(header_domain=shop_domain, payload_domain=payload_domain)

    
    # Process the webhook
    entry_id = await svc.receive_webhook(
        platform=WebhookPlatform.SHOPIFY,
        topic=topic,
        shop_domain=shop_domain,
        webhook_id=webhook_id,  # type: ignore
        payload=payload,
        correlation_id=ctx.correlation_id,
    )
    
    return WebhookResponse(success=True, webhook_id=entry_id)