
# services/webhook-service/src/api/v1/webhooks.py
import json
import uuid7
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge
import redis.asyncio as redis
import time

from shared.api import success_response, error_response
from shared.api.dependencies import RequestContextDep
from shared.messaging.jetstream_client import JetStreamClient
from ...config import ServiceConfig
from ...dependencies import ConfigDep, LifecycleDep, RedisClientDep
from ...services.webhook_service import WebhookService
from ...repositories.webhook_repository import WebhookRepository
from ...models.enums import normalize_topic_enum, WebhookPlatform
from ...schemas.webhook import WebhookResponse
from ...exceptions import (
    InvalidContentTypeError,
    PayloadTooLargeError,
    InvalidSignatureError,
    MissingHeadersError,
    DomainMismatchError,
    MalformedPayloadError,
    InvalidShopDomainError,
    IPNotAllowedError
)

router = APIRouter()

async def read_body_with_limit(request: Request, max_bytes: int = 2097152) -> bytes:
    """Read request body with size limit"""
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise PayloadTooLargeError(len(body), max_bytes)
    return bytes(body)


@router.post(
    "/shopify/webhooks/{topic_path:path}",
    response_model=WebhookResponse,
    responses={
        200: {"description": "Webhook received"},
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        413: {"description": "Payload too large"},
        422: {"description": "Unprocessable entity"}
    }
)
async def receive_shopify_webhook(
    request: Request,
    topic_path: str,
    ctx: RequestContextDep,
    config: ConfigDep,
    lifecycle: LifecycleDep,
    redis_client: RedisClientDep,
    content_type: str = Header(None, alias="Content-Type"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256"),
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_webhook_id: str = Header(None, alias="X-Shopify-Webhook-Id"),
    x_shopify_api_version: Optional[str] = Header(None, alias="X-Shopify-Api-Version"),
):
    """Receive and process Shopify webhook"""
    start_time = time.time()
    
    # Get dependencies
    webhook_service = WebhookService(config, lifecycle.logger)
    webhook_repo = lifecycle.webhook_repo
    messaging_client = lifecycle.messaging_client
    
    # Logging context
    log_context = {
        'request_id': ctx.request_id,
        'correlation_id': ctx.correlation_id,
        'path': topic_path,
        'webhook_id': x_shopify_webhook_id,
        'topic_raw': x_shopify_topic,
        'shop_domain': x_shopify_shop_domain
    }
    
    try:
        # 1. Content-Type validation
        if not webhook_service.validate_content_type(content_type):
            webhook_invalid_content_type_counter.labels(platform='shopify').inc()
            raise InvalidContentTypeError(content_type or '')
        
        # 2. Read body with size limit
        try:
            raw_body = await read_body_with_limit(request, config.webhook_body_limit)
            payload_bytes = len(raw_body)
        except PayloadTooLargeError as e:
            webhook_payload_too_large_counter.labels(platform='shopify').inc()
            raise
        
        # 3. Extract headers (case-insensitive)
        headers = webhook_service.extract_canonical_headers(dict(request.headers))
        
        # Update headers with explicitly provided values
        if x_shopify_hmac_sha256:
            headers['X-Shopify-Hmac-Sha256'] = x_shopify_hmac_sha256
        if x_shopify_topic:
            headers['X-Shopify-Topic'] = x_shopify_topic
        if x_shopify_shop_domain:
            headers['X-Shopify-Shop-Domain'] = x_shopify_shop_domain
        if x_shopify_webhook_id:
            headers['X-Shopify-Webhook-Id'] = x_shopify_webhook_id
        if x_shopify_api_version:
            headers['X-Shopify-Api-Version'] = x_shopify_api_version
        
        # 4. Validate required headers
        required_headers = [
            'X-Shopify-Hmac-Sha256',
            'X-Shopify-Topic',
            'X-Shopify-Shop-Domain',
            'X-Shopify-Webhook-Id'
        ]
        missing_headers = [h for h in required_headers if h not in headers]
        if missing_headers:
            webhook_missing_headers_counter.labels(platform='shopify').inc()
            lifecycle.logger.warning("Missing headers", extra={**log_context, 'missing': missing_headers})
            raise MissingHeadersError(missing_headers)
        
        # 5. HMAC validation
        hmac_source, valid = webhook_service.validate_hmac(
            raw_body,
            headers['X-Shopify-Hmac-Sha256'],
            config.shopify_api_secret,
            config.shopify_api_secret_next
        )
        
        if not valid:
            webhook_invalid_hmac_counter.labels(platform='shopify').inc()
            lifecycle.logger.warning("Invalid HMAC", extra=log_context)
            raise InvalidSignatureError()
        
        # Track HMAC validation
        webhook_hmac_validated_counter.labels(platform='shopify', secret=hmac_source).inc()
        if hmac_source == 'next':
            webhook_hmac_rotation_counter.labels(platform='shopify').inc()

       
        log_context['hmac_source'] = hmac_source

        # 6. Normalize values
        shop_domain = headers['X-Shopify-Shop-Domain'].lower()
        topic_raw = headers['X-Shopify-Topic']
        topic_enum = normalize_topic_enum(topic_raw)
        webhook_id = headers['X-Shopify-Webhook-Id']
        
        log_context['topic_enum'] = topic_enum
        
        # 7. Validate shop domain
        if not webhook_service.validate_shop_domain(shop_domain):
            webhook_domain_mismatch_counter.labels(platform='shopify').inc()
            lifecycle.logger.warning("Invalid domain suffix", extra=log_context)
            raise InvalidShopDomainError(shop_domain)
        
        # 8. IP allowlist check
        if config.webhook_ip_allowlist_mode != 'disabled':
            client_ip = request.client.host
            if not webhook_service.is_shopify_ip(client_ip):
                webhook_ip_not_allowed_counter.labels(platform='shopify').inc()
                if config.webhook_ip_allowlist_mode == 'hard':
                    lifecycle.logger.warning(
                        "IP not allowed (hard mode)",
                        extra={**log_context, 'ip': client_ip}
                    )
                    raise IPNotAllowedError(client_ip)
                else:  # soft mode
                    lifecycle.logger.warning(
                        "IP not allowed (soft mode)",
                        extra={**log_context, 'ip': client_ip}
                    )
        
        # 9. Idempotency check
        idempotency_key = f"wh:shopify:{webhook_id}"
        existing_id = await redis_client.get(idempotency_key)
        
        if existing_id:
            webhook_duplicate_counter.labels(platform='shopify', topic_enum=topic_enum).inc()
            lifecycle.logger.info("Duplicate webhook", extra=log_context)
            return WebhookResponse(success=True, webhook_id=existing_id.decode('utf-8'))
        
        # 10. Parse JSON
        try:
            payload = json.loads(raw_body)
        except Exception:
            webhook_failed_counter.labels(platform='shopify', topic_enum=topic_enum, reason='malformed_json').inc()
            lifecycle.logger.error("Malformed JSON", extra=log_context)
            raise MalformedPayloadError()
        
        # 11. Domain cross-check (only if present)
        if 'myshopify_domain' in payload:
            if payload['myshopify_domain'].lower() != shop_domain:
                webhook_domain_mismatch_counter.labels(platform='shopify').inc()
                lifecycle.logger.warning("Domain mismatch", extra=log_context)
                raise DomainMismatchError(
                    headers['X-Shopify-Shop-Domain'],
                    payload['myshopify_domain']
                )
        
        # 12. Capture headers for storage
        captured_headers = {
            'X-Shopify-Webhook-Id': webhook_id,
            'X-Shopify-Topic': topic_raw,
            'X-Shopify-Api-Version': headers.get('X-Shopify-Api-Version'),
            'X-Shopify-Shop-Domain': headers['X-Shopify-Shop-Domain'],
            'User-Agent': request.headers.get('user-agent'),
            'Content-Length': request.headers.get('content-length'),
            'X-Request-Id': ctx.request_id,
            'X-Correlation-Id': ctx.correlation_id
        }
        
        # 13. Store webhook
        try:
            webhook = await webhook_repo.create(
                platform=WebhookPlatform.SHOPIFY.value,
                topic_raw=topic_raw,
                topic_enum=topic_enum,
                shop_domain=shop_domain,
                webhook_id=webhook_id,
                api_version=headers.get('X-Shopify-Api-Version'),
                signature=headers['X-Shopify-Hmac-Sha256'],
                headers=captured_headers,
                payload=payload,
                payload_bytes=payload_bytes
            )
            
            # Set idempotency key
            await redis_client.set(
                idempotency_key,
                str(webhook.id),
                ex=config.webhook_idempotency_ttl
            )
            
            webhook_uuid = str(webhook.id)
            
        except Exception as e:
            # Fallback: publish to durable stream
            lifecycle.logger.error(
                "DB unavailable, using stream fallback",
                extra={**log_context, 'error': str(e)}
            )
            
            # Publish raw webhook to stream
            message_headers = {
                'request_id': ctx.request_id,
                'correlation_id': ctx.correlation_id,
                'webhook_id': webhook_id,
                'topic_enum': topic_enum,
                'shop_domain': shop_domain
            }
            
            ack = await messaging_client.js.publish(
                'webhook.shopify.received',
                json.dumps({
                    'headers': captured_headers,
                    'payload': payload,
                    'payload_bytes': payload_bytes,
                    'topic_raw': topic_raw,
                    'topic_enum': topic_enum,
                    'shop_domain': shop_domain,
                    'webhook_id': webhook_id,
                    'signature': headers['X-Shopify-Hmac-Sha256'],
                    'api_version': headers.get('X-Shopify-Api-Version'),
                    'timestamp': str(uuid7.uuid7())
                }).encode(),
                headers=message_headers
            )
            
            # Use webhook platform ID as response
            webhook_uuid = webhook_id
        
        # 14. Publish for async processing
        await messaging_client.js.publish(
            'webhook.shopify.process',
            json.dumps({
                'webhook_id': webhook_uuid,
                'request_id': ctx.request_id,
                'correlation_id': ctx.correlation_id
            }).encode(),
            headers={
                'request_id': ctx.request_id,
                'correlation_id': ctx.correlation_id,
                'webhook_id': webhook_id,
                'topic_enum': topic_enum,
                'shop_domain': shop_domain
            }
        )
        
        # 15. Metrics and response
        ack_latency = time.time() - start_time
        webhook_received_counter.labels(platform='shopify', topic_enum=topic_enum).inc()
        webhook_ack_latency_histogram.labels(platform='shopify', topic_enum=topic_enum).observe(ack_latency)
        webhook_payload_size_histogram.labels(platform='shopify', topic_enum=topic_enum).observe(payload_bytes)
        
        lifecycle.logger.info(
            "Webhook received",
            extra={**log_context, 'latency_ms': ack_latency * 1000}
        )
        
        return WebhookResponse(success=True, webhook_id=webhook_uuid)
        
    except (
        InvalidContentTypeError,
        PayloadTooLargeError,
        InvalidSignatureError,
        MissingHeadersError,
        DomainMismatchError,
        MalformedPayloadError,
        InvalidShopDomainError,
        IPNotAllowedError
    ) as e:
        # Known errors - return appropriate HTTP status
        if isinstance(e, InvalidContentTypeError):
            return JSONResponse(
                status_code=400,
                content={"error": str(e)},
                headers={"X-Correlation-Id": ctx.correlation_id}
            )
        elif isinstance(e, PayloadTooLargeError):
            return JSONResponse(
                status_code=413,
                content={"error": str(e)},
                headers={"X-Correlation-Id": ctx.correlation_id}
            )
        elif isinstance(e, InvalidSignatureError):
            return JSONResponse(
                status_code=401,
                content={"error": str(e)},
                headers={"X-Correlation-Id": ctx.correlation_id}
            )
        elif isinstance(e, MalformedPayloadError):
            return JSONResponse(
                status_code=422,
                content={"error": str(e)},
                headers={"X-Correlation-Id": ctx.correlation_id}
            )
        elif isinstance(e, IPNotAllowedError):
            return JSONResponse(
                status_code=403,
                content={"error": str(e)},
                headers={"X-Correlation-Id": ctx.correlation_id}
            )
        else:  # Other 400 errors
            return JSONResponse(
                status_code=400,
                content={"error": str(e)},
                headers={"X-Correlation-Id": ctx.correlation_id}
            )
            
    except Exception as e:
        lifecycle.logger.exception("Unexpected error", extra=log_context)
        webhook_failed_counter.labels(
            platform='shopify',
            topic_enum=log_context.get('topic_enum', 'unknown'),
            reason='unexpected_error'
        ).inc()
        return JSONResponse(
            status_code=500,
            content={"error": "Internal error"},
            headers={"X-Correlation-Id": ctx.correlation_id}
        )

