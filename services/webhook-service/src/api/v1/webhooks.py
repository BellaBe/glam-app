# services/webhook-service/src/api/v1/webhooks.py
import json

from fastapi import APIRouter

from shared.api.dependencies import ClientAuthDep, LoggerDep, PlatformContextDep, RequestContextDep, WebhookHeadersDep
from shared.api.validation import validate_shop_context

from ...dependencies import WebhookServiceDep
from ...exceptions import InvalidContentTypeError, MalformedPayloadError, PayloadTooLargeError
from ...models import WebhookPlatform, parse_topic
from ...schemas.webhooks import WebhookResponse

webhooks_router = APIRouter(prefix="/webhooks")


@webhooks_router.post("/shopify", response_model=WebhookResponse)
async def receive_shopify_webhook(
    body: bytes,
    svc: WebhookServiceDep,
    ctx: RequestContextDep,
    client_auth: ClientAuthDep,
    platform_ctx: PlatformContextDep,
    webhook: WebhookHeadersDep,
    logger: LoggerDep,
) -> WebhookResponse:
    """Receive webhook from Shopify BFF."""

    # Validate content type
    ct = (ctx.content_type or "").lower()
    if "application/json" not in ct:
        raise InvalidContentTypeError(ct)

    # Check payload size
    if len(body) > 2097152:  # 2MB limit
        raise PayloadTooLargeError(len(body), 2097152)

    # Parse the body
    try:
        payload = json.loads(body)
    except Exception as e:
        raise MalformedPayloadError() from e

    # ✨ Single validation call handles everything
    validate_shop_context(
        client_auth=client_auth,
        platform_ctx=platform_ctx,
        logger=logger,
        expected_platform="shopify",  # This is a Shopify-only endpoint
        expected_scope="bff:call",  # Required scope
        webhook_payload=payload,  # Validate payload domain
    )

    # Set logger context
    logger.set_request_context(
        platform=platform_ctx.platform,
        domain=platform_ctx.domain,
        webhook_topic=webhook.topic,
        webhook_id=webhook.webhook_id,
    )

    logger.info("Received Shopify webhook", extra={"correlation_id": ctx.correlation_id, "payload_size": len(body)})

    # Process the webhook
    entry_id = await svc.receive_webhook(
        platform=WebhookPlatform.SHOPIFY,
        topic=parse_topic(webhook.topic),
        shop_domain=platform_ctx.domain,
        webhook_id=webhook.webhook_id,
        payload=payload,
        correlation_id=ctx.correlation_id,
    )

    logger.info("Webhook processed successfully")

    return WebhookResponse(success=True, webhook_id=entry_id)
