# Webhook Service

Receives platform webhooks from the Shopify BFF and publishes domain events into the system.  
This service **does not** accept raw Shopify calls directly — all requests are relayed from the BFF with internal JWT authentication.

---

## Overview

### Responsibilities
- Accept webhook payloads from the BFF at a **single unified endpoint**:  
  `POST /api/v1/webhooks/shopify`
- Validate required headers and content type.
- Enforce a payload size limit.
- Store webhook records and ensure **idempotency** (via DB unique constraint on `webhook_id`).
- Publish mapped domain events for downstream services.

### Not in scope
- Shopify HMAC validation (done in BFF).
- Raw merchant access token handling (BFF handles platform auth).
- Redis-based idempotency (handled by DB uniqueness).

---

## Configuration

Environment variables:

| Name | Required | Description |
|------|----------|-------------|
| `INTERNAL_JWT_SECRET` | ✅ | Shared secret for internal JWT verification between BFF and this service. |
| `BODY_LIMIT_BYTES` | ❌ (default: `2097152`) | Maximum request body size in bytes (default 2 MB). |
| `SERVICE_PORT` | ❌ (default: `8000`) | Service HTTP port. |

---

## API

### **POST** `/api/v1/webhooks/shopify`

Receives a webhook payload from the BFF.

#### Required Headers
| Header | Description |
|--------|-------------|
| `Authorization` | `Bearer <JWT>` signed with `INTERNAL_JWT_SECRET` — must have `scope: "bff:call"`. |
| `Content-Type` | Must include `application/json`. |
| `X-Shopify-Shop-Domain` | Shop domain (e.g., `test-shop.myshopify.com`). |
| `X-Shopify-Topic` | Shopify webhook topic (e.g., `orders/create`). |
| `X-Shopify-Webhook-Id` | Unique webhook delivery ID from Shopify. |

#### Request Body
- JSON payload exactly as received from Shopify (via BFF).

#### Responses
| Status | When |
|--------|------|
| `200 OK` | Webhook accepted (new or duplicate). Returns `{ "success": true, "webhook_id": "<uuid>" }`. |
| `400 Bad Request` | Missing or invalid headers, payload not JSON, or content type not `application/json`. |
| `403 Forbidden` | JWT scope not `bff:call` or shop domain mismatch with JWT. |
| `413 Payload Too Large` | Body exceeds configured limit. |

---

## Webhook Processing Flow

1. **Shopify → BFF**  
   Shopify delivers webhook to your Remix BFF endpoint.  
   The BFF validates HMAC, extracts the payload + headers, signs an internal JWT, and relays to this service.

2. **BFF → Webhook Service**  
   - Calls `POST /api/v1/webhooks/shopify`
   - Passes original Shopify headers (`topic`, `shop domain`, `webhook id`).
   - Uses `Authorization: Bearer <internal-jwt>` signed with `INTERNAL_JWT_SECRET`.

3. **Webhook Service**  
   - Validates JWT, headers, and payload size.
   - Stores the webhook in the database.
   - If duplicate (`webhook_id` already stored) → logs and returns success without re-publishing.
   - If new → publishes mapped domain event via `WebhookEventPublisher`.

---

## Example Request (curl)

```bash
curl -X POST http://localhost:8112/api/v1/webhooks/shopify \
  -H "Authorization: Bearer $(jwtgen)" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Topic: orders/create" \
  -H "X-Shopify-Shop-Domain: test-shop.myshopify.com" \
  -H "X-Shopify-Webhook-Id: webhook-123456" \
  -d '{
        "id": 123456789,
        "total_price": "10.00",
        "currency": "USD",
        "created_at": "2025-08-09T12:00:00Z",
        "line_items": []
      }'

**Note**  
`jwtgen` above is a placeholder for generating a valid JWT with payload:
```json
{
  "sub": "test-shop.myshopify.com",
  "scope": "bff:call",
  "iat": 1691587200
}
```

Sign it using **HS256** with `INTERNAL_JWT_SECRET`.

### Event Mapping

| Shopify Topic                       | Domain Event                         |
|------------------------------------|--------------------------------------|
| `app/uninstalled`                  | `app_uninstalled`                    |
| `orders/create`                    | `order_created`                      |
| `app_subscriptions/update`         | `app_subscription_updated`           |
| `app_purchases_one_time/update`    | `app_purchase_updated`               |
| `products/create`                  | `catalog_product_event (created)`    |
| `products/update`                  | `catalog_product_event (updated)`    |
| `products/delete`                  | `catalog_product_event (deleted)`    |
| `collections/create`               | `catalog_collection_event (created)` |
| `collections/update`               | `catalog_collection_event (updated)` |
| `collections/delete`               | `catalog_collection_event (deleted)` |
| `inventory_levels/update`          | `inventory_updated`                  |
| `customers/data_request`           | `gdpr_data_request`                  |
| `customers/redact`                 | `gdpr_customer_redact`               |
| `shop/redact`                      | `gdpr_shop_redact`                   |
| *(unknown)*                        | Logged as warning; no event published |

### Local Development

Run with Docker:
```bash
docker compose up webhook-service
```

Test locally (with valid JWT):

```bash
python scripts/test_webhook.py
```

```bash
python scripts/test_webhook.py
```
This way the part after the curl example won’t break the Markdown structure again.
  