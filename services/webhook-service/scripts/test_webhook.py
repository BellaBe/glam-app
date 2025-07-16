# services/webhook-service/scripts/test_webhook.py
#!/usr/bin/env python3
"""
Test script for webhook service.

This script sends sample webhooks to the webhook service for testing.
"""

import json
import hmac
import hashlib
import base64
import requests
from datetime import datetime

# Configuration
WEBHOOK_SERVICE_URL = "http://localhost:8012"
SHOPIFY_SECRET = "test_secret_key"  # Should match your .env

def create_shopify_signature(body: str, secret: str) -> str:
    """Create Shopify HMAC signature."""
    calculated = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(calculated).decode()

def test_shopify_product_create():
    """Test Shopify product create webhook."""
    
    payload = {
        "id": 123456789,
        "title": "Test Product",
        "handle": "test-product",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "shop": {
            "domain": "test-shop.myshopify.com",
            "id": 987654321
        }
    }
    
    body = json.dumps(payload)
    signature = create_shopify_signature(body, SHOPIFY_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Topic": "products/create",
        "X-Shopify-Hmac-Sha256": signature,
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-API-Version": "2024-01",
        "X-Shopify-Webhook-Id": "12345678-1234-1234-1234-123456789012"
    }
    
    print("Testing Shopify product create webhook...")
    
    # Test topic in URL
    response = requests.post(
        f"{WEBHOOK_SERVICE_URL}/webhooks/shopify/products/create",
        headers=headers,
        data=body
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ Webhook processed successfully!")
    else:
        print("❌ Webhook processing failed!")
    
    return response.status_code == 200

def test_shopify_order_create():
    """Test Shopify order create webhook."""
    
    payload = {
        "id": 456789123,
        "order_number": 1001,
        "total_price": "29.99",
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "line_items": [
            {
                "id": 789123456,
                "product_id": 123456789,
                "quantity": 1,
                "price": "29.99"
            }
        ],
        "customer": {
            "id": 321654987,
            "email": "customer@example.com"
        },
        "shop": {
            "domain": "test-shop.myshopify.com",
            "id": 987654321
        }
    }
    
    body = json.dumps(payload)
    signature = create_shopify_signature(body, SHOPIFY_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Hmac-Sha256": signature,
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-API-Version": "2024-01",
        "X-Shopify-Webhook-Id": "87654321-4321-4321-4321-210987654321"
    }
    
    print("\nTesting Shopify order create webhook...")
    
    # Test generic endpoint
    response = requests.post(
        f"{WEBHOOK_SERVICE_URL}/webhooks/shopify",
        headers=headers,
        data=body
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ Webhook processed successfully!")
    else:
        print("❌ Webhook processing failed!")
    
    return response.status_code == 200

def test_health_check():
    """Test health check endpoint."""
    
    print("\nTesting health check...")
    
    response = requests.get(f"{WEBHOOK_SERVICE_URL}/api/v1/health")
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ Health check passed!")
    else:
        print("❌ Health check failed!")
    
    return response.status_code == 200

def test_invalid_signature():
    """Test webhook with invalid signature."""
    
    payload = {"test": "data"}
    body = json.dumps(payload)
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Topic": "products/create",
        "X-Shopify-Hmac-Sha256": "invalid_signature",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-API-Version": "2024-01",
        "X-Shopify-Webhook-Id": "test-id"
    }
    
    print("\nTesting invalid signature...")
    
    response = requests.post(
        f"{WEBHOOK_SERVICE_URL}/webhooks/shopify/products/create",
        headers=headers,
        data=body
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 401:
        print("✅ Invalid signature properly rejected!")
        return True
    else:
        print("❌ Invalid signature not properly handled!")
        return False

def main():
    """Run all tests."""
    
    print("🧪 Starting webhook service tests...\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Shopify Product Create", test_shopify_product_create),
        ("Shopify Order Create", test_shopify_order_create),
        ("Invalid Signature", test_invalid_signature),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the webhook service logs for details.")

if __name__ == "__main__":
    main()
