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
    os.environ["ENVIRONMENT"] = "test"
    os.environ["CREDIT_DB_PASSWORD"] = "test_password"
    os.environ["CREDIT_ADMIN_TOKEN"] = "test_admin_token"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture(scope="session")
async def postgres_container():
    """PostgreSQL test container"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        db_url = postgres.get_connection_url()
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

