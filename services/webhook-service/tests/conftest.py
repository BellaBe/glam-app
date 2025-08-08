import pytest
import pytest_asyncio
import os
import uuid7
from pathlib import Path
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from prisma import Prisma
from shared.api.correlation import set_correlation_context


@pytest.fixture(scope="session", autouse=True)
def setup_test_config():
    """Set up test configuration"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["SHOPIFY_API_SECRET"] = "test_webhook_secret"
    os.environ["SHOPIFY_API_SECRET_NEXT"] = "test_rotation_secret"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def postgres_container():
    """PostgreSQL test container"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        # Set DATABASE_URL for Prisma
        db_url = postgres.get_connection_url()
        # Replace psycopg2 with asyncpg for Prisma
        db_url = db_url.replace("psycopg2", "asyncpg")
        os.environ["DATABASE_URL"] = db_url
        
        yield postgres


@pytest_asyncio.fixture(scope="session")
async def redis_container():
    """Redis test container"""
    with RedisContainer("redis:7-alpine") as redis:
        os.environ["REDIS_URL"] = redis.get_connection_url()
        yield redis


@pytest_asyncio.fixture
async def prisma_client(postgres_container):
    """Test Prisma client"""
    client = Prisma()
    await client.connect()
    
    # Run migrations for tests
    import subprocess
    subprocess.run(["prisma", "db", "push", "--skip-generate"], check=True)
    
    yield client
    
    # Cleanup
    await client.disconnect()


@pytest_asyncio.fixture
async def client(prisma_client, redis_container):
    """Test client with correlation context"""
    from src.main import app
    
    app.state.test_mode = True
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def correlation_context():
    """Set up correlation context for tests"""
    correlation_id = str(uuid7.uuid7())
    set_correlation_context(correlation_id)
    
    return {
        "correlation_id": correlation_id
    }


@pytest.fixture
def valid_shopify_webhook():
    """Valid Shopify webhook payload"""
    return {
        "id": 123456789,
        "email": "test@example.com",
        "closed_at": None,
        "created_at": "2024-01-15T10:00:00-05:00",
        "updated_at": "2024-01-15T10:00:00-05:00",
        "number": 1,
        "note": None,
        "token": "abcdef123456",
        "gateway": "manual",
        "test": True,
        "total_price": "100.00",
        "subtotal_price": "90.00",
        "total_weight": 0,
        "total_tax": "10.00",
        "taxes_included": True,
        "currency": "USD",
        "financial_status": "paid",
        "confirmed": True,
        "total_discounts": "0.00",
        "total_line_items_price": "90.00",
        "cart_token": None,
        "buyer_accepts_marketing": False,
        "name": "#1001",
        "referring_site": None,
        "landing_site": None,
        "cancelled_at": None,
        "cancel_reason": None,
        "total_price_usd": "100.00",
        "checkout_token": None,
        "reference": None,
        "user_id": None,
        "location_id": None,
        "source_identifier": None,
        "source_url": None,
        "processed_at": "2024-01-15T10:00:00-05:00",
        "device_id": None,
        "phone": None,
        "customer_locale": "en",
        "app_id": 123456,
        "browser_ip": "192.168.1.1",
        "client_details": {
            "browser_ip": "192.168.1.1",
            "accept_language": "en-US,en;q=0.9",
            "user_agent": "Mozilla/5.0",
            "session_hash": None,
            "browser_width": 1920,
            "browser_height": 1080
        },
        "line_items": [
            {
                "id": 987654321,
                "variant_id": 456789123,
                "title": "Test Product",
                "quantity": 1,
                "sku": "TEST-001",
                "variant_title": None,
                "vendor": "Test Vendor",
                "fulfillment_service": "manual",
                "product_id": 789123456,
                "requires_shipping": True,
                "taxable": True,
                "gift_card": False,
                "name": "Test Product",
                "variant_inventory_management": "shopify",
                "properties": [],
                "product_exists": True,
                "fulfillable_quantity": 1,
                "grams": 200,
                "price": "90.00",
                "total_discount": "0.00",
                "fulfillment_status": None,
                "price_set": {
                    "shop_money": {
                        "amount": "90.00",
                        "currency_code": "USD"
                    }
                },
                "total_discount_set": {
                    "shop_money": {
                        "amount": "0.00",
                        "currency_code": "USD"
                    }
                },
                "discount_allocations": [],
                "tax_lines": []
            }
        ],
        "myshopify_domain": "test-shop.myshopify.com"
    }


@pytest.fixture
def shopify_headers():
    """Valid Shopify webhook headers"""
    return {
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Hmac-Sha256": "will-be-calculated",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-Webhook-Id": str(uuid7.uuid7()),
        "X-Shopify-Api-Version": "2024-01",
        "Content-Type": "application/json"
    }


