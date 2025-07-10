# services/credit-service/tests/conftest.py
"""Test configuration and fixtures for credit service."""

import asyncio
import pytest
import pytest_asyncio
from decimal import Decimal
from uuid import uuid4
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from shared.database.base import Base
from shared.utils.logger import create_logger

from src.config import CreditServiceConfig
from src.models import CreditAccount, CreditTransaction, TransactionType, ReferenceType
from src.repositories.credit_account_repository import CreditAccountRepository
from src.repositories.credit_transaction_repository import CreditTransactionRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL container for testing."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session") 
async def redis_container():
    """Start Redis container for testing."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
async def test_config(postgres_container, redis_container):
    """Create test configuration."""
    return CreditServiceConfig(
        DATABASE_URL=postgres_container.get_connection_url().replace("psycopg2", "asyncpg"),
        REDIS_URL=redis_container.get_connection_url(),
        NATS_URL="nats://localhost:4222",  # Mock or skip in tests
        TRIAL_CREDITS=Decimal("100.00"),
        LOG_LEVEL="DEBUG"
    )


@pytest_asyncio.fixture
async def db_session(test_config) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    engine = create_async_engine(test_config.DATABASE_URL)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def test_merchant_id():
    """Create test merchant ID."""
    return uuid4()


@pytest.fixture
async def test_account(db_session: AsyncSession, test_merchant_id) -> CreditAccount:
    """Create test credit account."""
    account = CreditAccount(
        merchant_id=test_merchant_id,
        balance=Decimal("50.00"),
        lifetime_credits=Decimal("100.00")
    )
    
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    
    return account


@pytest.fixture 
async def credit_account_repo(db_session: AsyncSession) -> CreditAccountRepository:
    """Create credit account repository."""
    session_factory = async_sessionmaker(bind=db_session.bind)
    return CreditAccountRepository(session_factory)


@pytest.fixture
async def credit_transaction_repo(db_session: AsyncSession) -> CreditTransactionRepository:
    """Create credit transaction repository.""" 
    session_factory = async_sessionmaker(bind=db_session.bind)
    return CreditTransactionRepository(session_factory)


@pytest.fixture
def logger():
    """Create test logger."""
    return create_logger("credit-service-test", "DEBUG")