# ruff: noqa: T201
"""Manual test script for webhook service"""
import asyncio
import base64
import hashlib
import hmac
import json
from datetime import datetime

import httpx
import uuid7


def compute_hmac(body: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 for webhook body"""
    hash_obj = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
    return base64.b64encode(hash_obj.digest()).decode("utf-8")


async def test_order_webhook():
    """Test order created webhook"""
    # Webhook payload
    payload = {
        "id": 5678901234,
        "email": "customer@example.com",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "total_price": "150.00",
        "currency": "USD",
        "financial_status": "paid",
        "line_items": [
            {"id": 111, "title": "Test Product 1", "quantity": 2, "price": "50.00"},
            {"id": 222, "title": "Test Product 2", "quantity": 1, "price": "50.00"},
        ],
        "myshopify_domain": "test-shop.myshopify.com",
    }

    body = json.dumps(payload).encode()

    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-Webhook-Id": str(uuid7.uuid7()),
        "X-Shopify-Api-Version": "2024-01",
        "X-Shopify-Hmac-Sha256": compute_hmac(body, "your-shopify-webhook-secret"),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8112/api/v1/shopify/webhooks/orders/create", content=body, headers=headers
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print(f"Headers: {dict(response.headers)}")


async def test_app_uninstalled_webhook():
    """Test app uninstalled webhook"""
    payload = {
        "id": 1234567890,
        "name": "Test Shop",
        "email": "shop@example.com",
        "domain": "test-shop.myshopify.com",
        "created_at": "2024-01-01T00:00:00Z",
        "myshopify_domain": "test-shop.myshopify.com",
    }

    body = json.dumps(payload).encode()

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Topic": "app/uninstalled",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-Webhook-Id": str(uuid7.uuid7()),
        "X-Shopify-Api-Version": "2024-01",
        "X-Shopify-Hmac-Sha256": compute_hmac(body, "your-shopify-webhook-secret"),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8112/api/v1/shopify/webhooks/app/uninstalled", content=body, headers=headers
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_duplicate_webhook():
    """Test duplicate webhook handling"""
    webhook_id = str(uuid7.uuid7())
    payload = {"test": "duplicate"}
    body = json.dumps(payload).encode()

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-Webhook-Id": webhook_id,  # Same ID for both requests
        "X-Shopify-Api-Version": "2024-01",
        "X-Shopify-Hmac-Sha256": compute_hmac(body, "your-shopify-webhook-secret"),
    }

    async with httpx.AsyncClient() as client:
        # First request
        response1 = await client.post(
            "http://localhost:8112/api/v1/shopify/webhooks/test", content=body, headers=headers
        )
        print(f"First request - Status: {response1.status_code}, Response: {response1.json()}")

        # Second request with same webhook ID
        response2 = await client.post(
            "http://localhost:8112/api/v1/shopify/webhooks/test", content=body, headers=headers
        )
        print(f"Second request - Status: {response2.status_code}, Response: {response2.json()}")


async def test_health_check():
    """Test health endpoints"""
    async with httpx.AsyncClient() as client:
        # Basic health
        response = await client.get("http://localhost:8112/api/v1/health")
        print(f"Basic health: {response.json()}")

        # Detailed health
        response = await client.get("http://localhost:8112/api/v1/health/detailed")
        print(f"Detailed health: {json.dumps(response.json(), indent=2)}")


async def main():
    print("Testing Webhook Service...")
    print("\n1. Testing Order Created Webhook:")
    await test_order_webhook()

    print("\n2. Testing App Uninstalled Webhook:")
    await test_app_uninstalled_webhook()

    print("\n3. Testing Duplicate Webhook:")
    await test_duplicate_webhook()

    print("\n4. Testing Health Checks:")
    await test_health_check()


if __name__ == "__main__":
    asyncio.run(main())
