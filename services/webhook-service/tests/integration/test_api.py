import pytest
import json
import hmac
import hashlib
import base64
import uuid7
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.fixture
def compute_hmac():
    """Helper to compute HMAC for tests"""
    def _compute(body: bytes, secret: str) -> str:
        hash_obj = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        )
        return base64.b64encode(hash_obj.digest()).decode('utf-8')
    return _compute


async def test_receive_webhook_success(client: AsyncClient, valid_shopify_webhook, shopify_headers, compute_hmac):
    """Test successful webhook reception"""
    body = json.dumps(valid_shopify_webhook).encode()
    
    # Compute valid HMAC
    shopify_headers["X-Shopify-Hmac-Sha256"] = compute_hmac(body, "test_webhook_secret")
    
    # Mock Redis to simulate no duplicate
    with patch('redis.asyncio.Redis.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.post(
            "/api/v1/shopify/webhooks/orders/create",
            content=body,
            headers=shopify_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "webhook_id" in data


async def test_receive_webhook_invalid_content_type(client: AsyncClient, valid_shopify_webhook, shopify_headers):
    """Test webhook with invalid content type"""
    body = json.dumps(valid_shopify_webhook).encode()
    
    # Set invalid content type
    shopify_headers["Content-Type"] = "text/plain"
    
    response = await client.post(
        "/api/v1/shopify/webhooks/orders/create",
        content=body,
        headers=shopify_headers
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Content-Type must be application/json" in data["error"]


async def test_receive_webhook_invalid_hmac(client: AsyncClient, valid_shopify_webhook, shopify_headers):
    """Test webhook with invalid HMAC"""
    body = json.dumps(valid_shopify_webhook).encode()
    
    # Set invalid HMAC
    shopify_headers["X-Shopify-Hmac-Sha256"] = "invalid_hmac"
    
    response = await client.post(
        "/api/v1/shopify/webhooks/orders/create",
        content=body,
        headers=shopify_headers
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "Invalid HMAC signature" in data["error"]


async def test_receive_webhook_rotation_secret(client: AsyncClient, valid_shopify_webhook, shopify_headers, compute_hmac):
    """Test webhook validation with rotation secret"""
    body = json.dumps(valid_shopify_webhook).encode()
    
    # Compute HMAC with rotation secret
    shopify_headers["X-Shopify-Hmac-Sha256"] = compute_hmac(body, "test_rotation_secret")
    
    # Mock Redis
    with patch('redis.asyncio.Redis.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.post(
            "/api/v1/shopify/webhooks/orders/create",
            content=body,
            headers=shopify_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


async def test_receive_webhook_duplicate(client: AsyncClient, valid_shopify_webhook, shopify_headers, compute_hmac):
    """Test duplicate webhook handling"""
    body = json.dumps(valid_shopify_webhook).encode()
    
    # Compute valid HMAC
    shopify_headers["X-Shopify-Hmac-Sha256"] = compute_hmac(body, "test_webhook_secret")
    
    # Mock Redis to simulate duplicate
    with patch('redis.asyncio.Redis.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = b"existing-webhook-id"
        
        response = await client.post(
            "/api/v1/shopify/webhooks/orders/create",
            content=body,
            headers=shopify_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["webhook_id"] == "existing-webhook-id"


async def test_receive_webhook_missing_headers(client: AsyncClient, valid_shopify_webhook):
    """Test webhook with missing required headers"""
    body = json.dumps(valid_shopify_webhook).encode()
    
    # Only partial headers
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Topic": "orders/create"
    }
    
    response = await client.post(
        "/api/v1/shopify/webhooks/orders/create",
        content=body,
        headers=headers
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Required headers missing" in data["error"]


async def test_receive_webhook_payload_too_large(client: AsyncClient, shopify_headers, compute_hmac):
    """Test webhook with payload exceeding size limit"""
    # Create a large payload (> 2MB)
    large_data = {"data": "x" * (2 * 1024 * 1024 + 1)}
    body = json.dumps(large_data).encode()
    
    shopify_headers["X-Shopify-Hmac-Sha256"] = compute_hmac(body, "test_webhook_secret")
    
    response = await client.post(
        "/api/v1/shopify/webhooks/orders/create",
        content=body,
        headers=shopify_headers
    )
    
    assert response.status_code == 413
    data = response.json()
    assert "exceeds" in data["error"] and "limit" in data["error"]


async def test_receive_webhook_invalid_json(client: AsyncClient, shopify_headers, compute_hmac):
    """Test webhook with malformed JSON"""
    body = b'{"invalid": json}'
    
    shopify_headers["X-Shopify-Hmac-Sha256"] = compute_hmac(body, "test_webhook_secret")
    
    # Mock Redis
    with patch('redis.asyncio.Redis.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.post(
            "/api/v1/shopify/webhooks/orders/create",
            content=body,
            headers=shopify_headers
        )
    
    assert response.status_code == 422
    data = response.json()
    assert "Invalid JSON payload" in data["error"]


async def test_receive_webhook_domain_mismatch(client: AsyncClient, shopify_headers, compute_hmac):
    """Test webhook with domain mismatch between header and payload"""
    payload = {
        "id": 123,
        "myshopify_domain": "other-shop.myshopify.com"  # Different from header
    }
    body = json.dumps(payload).encode()
    
    shopify_headers["X-Shopify-Hmac-Sha256"] = compute_hmac(body, "test_webhook_secret")
    
    # Mock Redis
    with patch('redis.asyncio.Redis.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.post(
            "/api/v1/shopify/webhooks/orders/create",
            content=body,
            headers=shopify_headers
        )
    
    assert response.status_code == 400
    data = response.json()
    assert "Shop domain mismatch" in data["error"]


async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


async def test_health_detailed_endpoint(client: AsyncClient):
    """Test detailed health check endpoint"""
    response = await client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "components" in data
    assert "timestamp" in data


