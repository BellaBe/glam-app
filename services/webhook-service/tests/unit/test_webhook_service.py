import pytest
import hmac
import hashlib
import base64
import json
from src.services.webhook_service import WebhookService
from src.config import ServiceConfig
from shared.utils.logger import create_logger


@pytest.fixture
def test_config():
    """Test configuration"""
    return ServiceConfig(
        service_name="webhook-service",
        service_version="1.0.0",
        environment="test",
        api_host="localhost",
        api_port=8012,
        api_external_port=8112,
        api_cors_origins=["*"],
        nats_url="nats://localhost:4222",
        redis_url="redis://localhost:6379",
        logging_level="DEBUG",
        logging_format="json",
        logging_file_path="/tmp/test.log",
        monitoring_metrics_enabled=True,
        monitoring_tracing_enabled=False,
        rate_limiting_enabled=False,
        rate_limiting_window_seconds=60,
        db_enabled=True,
        database_url="postgresql://test@localhost/test",
        shopify_api_secret="test_secret",
        shopify_api_secret_next="test_secret_next"
    )


@pytest.fixture
def webhook_service(test_config):
    logger = create_logger("test")
    return WebhookService(test_config, logger)


def test_validate_hmac_with_primary_secret(webhook_service):
    """Test HMAC validation with primary secret"""
    raw_body = b'{"test": "data"}'
    secret = "test_secret"
    
    # Calculate correct HMAC
    hash_obj = hmac.new(
        secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    )
    correct_hmac = base64.b64encode(hash_obj.digest()).decode('utf-8')
    
    # Test validation
    source, valid = webhook_service.validate_hmac(
        raw_body,
        correct_hmac,
        secret,
        None
    )
    
    assert valid is True
    assert source == 'primary'


def test_validate_hmac_with_rotation_secret(webhook_service):
    """Test HMAC validation with rotation secret"""
    raw_body = b'{"test": "data"}'
    primary_secret = "test_secret"
    next_secret = "test_secret_next"
    
    # Calculate HMAC with next secret
    hash_obj = hmac.new(
        next_secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    )
    correct_hmac = base64.b64encode(hash_obj.digest()).decode('utf-8')
    
    # Test validation
    source, valid = webhook_service.validate_hmac(
        raw_body,
        correct_hmac,
        primary_secret,
        next_secret
    )
    
    assert valid is True
    assert source == 'next'


def test_validate_hmac_invalid(webhook_service):
    """Test HMAC validation with invalid signature"""
    raw_body = b'{"test": "data"}'
    
    # Test validation with wrong HMAC
    source, valid = webhook_service.validate_hmac(
        raw_body,
        "invalid_hmac",
        "test_secret",
        None
    )
    
    assert valid is False
    assert source is None


def test_validate_content_type(webhook_service):
    """Test content type validation"""
    # Valid content types
    assert webhook_service.validate_content_type("application/json") is True
    assert webhook_service.validate_content_type("application/json; charset=utf-8") is True
    assert webhook_service.validate_content_type("APPLICATION/JSON") is True
    
    # Invalid content types
    assert webhook_service.validate_content_type("text/plain") is False
    assert webhook_service.validate_content_type("") is False
    assert webhook_service.validate_content_type(None) is False


def test_validate_shop_domain(webhook_service):
    """Test shop domain validation"""
    # Valid domains
    assert webhook_service.validate_shop_domain("test-shop.myshopify.com") is True
    assert webhook_service.validate_shop_domain("TEST-SHOP.MYSHOPIFY.COM") is True
    
    # Invalid domains
    assert webhook_service.validate_shop_domain("test-shop.com") is False
    assert webhook_service.validate_shop_domain("myshopify.com") is False
    assert webhook_service.validate_shop_domain("") is False


def test_extract_canonical_headers(webhook_service):
    """Test header extraction and canonicalization"""
    headers = {
        "x-shopify-hmac-sha256": "test_hmac",
        "X-SHOPIFY-TOPIC": "orders/create",
        "x-shopify-shop-domain": "test.myshopify.com",
        "X-Shopify-Webhook-Id": "123",
        "x-shopify-api-version": "2024-01",
        "content-type": "application/json",
        "other-header": "value"
    }
    
    canonical = webhook_service.extract_canonical_headers(headers)
    
    assert canonical == {
        "X-Shopify-Hmac-Sha256": "test_hmac",
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Shop-Domain": "test.myshopify.com",
        "X-Shopify-Webhook-Id": "123",
        "X-Shopify-Api-Version": "2024-01"
    }


