#!/usr/bin/env python3
"""
Test script for webhook service.

Usage:
    python scripts/test_webhook.py
"""

import asyncio
import hashlib
import hmac
import base64
import json
import httpx
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
WEBHOOK_SERVICE_URL = os.getenv("WEBHOOK_SERVICE_URL", "http://localhost:8012")
SHOPIFY_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "test-secret")


def generate_shopify_hmac(body: bytes, secret: str) -> str:
    """Generate Shopify HMAC signature"""
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


async def test_shopify_webhook():
    """Test Shopify webhook"""
    
    # Sample product update webhook
    webhook_data = {
        "id": 1234567890,
        "title": "Test Product",
        "vendor": "Test Vendor",
        "product_type": "Test Type",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "status": "active",
        "variants": [
            {
                "id": 9876543210,
                "product_id": 1234567890,
                "title": "Default",
                "price": "19.99",
                "sku": "TEST-001",
                "inventory_quantity": 100
            }
        ]
    }
    
    body = json.dumps(webhook_data).encode()
    signature = generate_shopify_hmac(body, SHOPIFY_SECRET)
    
    headers = {
        "X-Shopify-Topic": "products/update",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-Webhook-Id": f"test-webhook-{datetime.utcnow().timestamp()}",
        "X-Shopify-Hmac-SHA256": signature,
        "X-Shopify-API-Version": "2024-01",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print(f"Sending webhook to {WEBHOOK_SERVICE_URL}/api/v1/webhooks/shopify/products/update")
        
        response = await client.post(
            f"{WEBHOOK_SERVICE_URL}/api/v1/webhooks/shopify/products/update",
            content=body,
            headers=headers
        )
        
        print(f"Response: {response.status_code}")
        if response.status_code != 200:
            print(f"Response body: {response.text}")
        
        # Test health check
        health_response = await client.get(f"{WEBHOOK_SERVICE_URL}/api/v1/health")
        print(f"\nHealth check: {health_response.json()}")


async def test_duplicate_webhook():
    """Test duplicate webhook handling"""
    
    webhook_data = {
        "id": 9999999999,
        "name": "Duplicate Order Test",
        "total_price": "99.99"
    }
    
    body = json.dumps(webhook_data).encode()
    signature = generate_shopify_hmac(body, SHOPIFY_SECRET)
    
    headers = {
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-Webhook-Id": "duplicate-test-123",  # Same ID for both requests
        "X-Shopify-Hmac-SHA256": signature,
        "X-Shopify-API-Version": "2024-01",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print("\n\nTesting duplicate webhook handling...")
        
        # First request
        print("Sending first webhook...")
        response1 = await client.post(
            f"{WEBHOOK_SERVICE_URL}/api/v1/webhooks/shopify",
            content=body,
            headers=headers
        )
        print(f"First response: {response1.status_code}")
        
        # Second request (duplicate)
        print("Sending duplicate webhook...")
        response2 = await client.post(
            f"{WEBHOOK_SERVICE_URL}/api/v1/webhooks/shopify",
            content=body,
            headers=headers
        )
        print(f"Second response: {response2.status_code} (should still be 200)")


async def test_invalid_signature():
    """Test invalid signature handling"""
    
    webhook_data = {"test": "invalid"}
    body = json.dumps(webhook_data).encode()
    
    headers = {
        "X-Shopify-Topic": "products/create",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-Webhook-Id": "invalid-test-123",
        "X-Shopify-Hmac-SHA256": "invalid-signature",
        "X-Shopify-API-Version": "2024-01",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print("\n\nTesting invalid signature...")
        
        response = await client.post(
            f"{WEBHOOK_SERVICE_URL}/api/v1/webhooks/shopify",
            content=body,
            headers=headers
        )
        print(f"Response: {response.status_code} (should be 401)")


async def main():
    """Run all tests"""
    print("Testing Webhook Service")
    print("=" * 50)
    
    await test_shopify_webhook()
    await test_duplicate_webhook()
    await test_invalid_signature()
    
    print("\n\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(main())