import pytest
import uuid7
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.services.credit_service import CreditService
from src.schemas.credit import CreditGrantIn, BalanceOut

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.get_balance = AsyncMock()
    repo.grant_credits_transactional = AsyncMock()
    repo.get_or_create_merchant_credit = AsyncMock()
    return repo

@pytest.fixture
def mock_publisher():
    publisher = AsyncMock()
    publisher.balance_changed = AsyncMock()
    publisher.balance_low = AsyncMock()
    publisher.balance_depleted = AsyncMock()
    return publisher

@pytest.fixture
def test_service(mock_repo, mock_publisher):
    from shared.utils.logger import create_logger
    logger = create_logger("test")
    config = MagicMock()
    config.trial_credits = 100
    config.low_balance_threshold = 20
    config.cache_enabled = False
    
    return CreditService(
        config=config,
        repository=mock_repo,
        publisher=mock_publisher,
        logger=logger,
        redis_client=None
    )

class MockContext:
    def __init__(self):
        self.correlation_id = str(uuid7.uuid7())

async def test_grant_credits_success(test_service, mock_repo, mock_publisher):
    """Test successful credit grant"""
    # Arrange
    ctx = MockContext()
    grant = CreditGrantIn(
        shop_domain="test.myshopify.com",
        amount=50,
        reason="manual",
        external_ref="test-123"
    )
    
    mock_repo.get_balance.return_value = BalanceOut(balance=100, updated_at=datetime.utcnow())
    mock_repo.grant_credits_transactional.return_value = (150, False)
    
    # Act
    result = await test_service.grant_credits(grant, ctx)
    
    # Assert
    assert result.ok is True
    assert result.balance == 150
    assert result.idempotent is False
    
    # Verify publisher called
    mock_publisher.balance_changed.assert_called_once()

async def test_grant_credits_idempotent(test_service, mock_repo, mock_publisher):
    """Test idempotent credit grant"""
    # Arrange
    ctx = MockContext()
    grant = CreditGrantIn(
        shop_domain="test.myshopify.com",
        amount=50,
        reason="manual",
        external_ref="test-123"
    )
    
    mock_repo.get_balance.return_value = BalanceOut(balance=150, updated_at=datetime.utcnow())
    mock_repo.grant_credits_transactional.return_value = (150, True)
    
    # Act
    result = await test_service.grant_credits(grant, ctx)
    
    # Assert
    assert result.ok is True
    assert result.balance == 150
    assert result.idempotent is True
    
    # Verify publisher not called for idempotent grant
    mock_publisher.balance_changed.assert_not_called()

async def test_low_balance_threshold(test_service, mock_repo, mock_publisher):
    """Test low balance threshold event"""
    # Arrange
    ctx = MockContext()
    grant = CreditGrantIn(
        shop_domain="test.myshopify.com",
        amount=10,
        reason="manual"
    )
    
    # Balance goes from 25 to 15 (crosses 20 threshold)
    mock_repo.get_balance.return_value = BalanceOut(balance=25, updated_at=datetime.utcnow())
    mock_repo.grant_credits_transactional.return_value = (15, False)
    
    # Act
    await test_service.grant_credits(grant, ctx)
    
    # Assert
    mock_publisher.balance_low.assert_called_once_with(
        shop_domain="test.myshopify.com",
        balance=15,
        threshold=20,
        correlation_id=ctx.correlation_id
    )

async def test_balance_depleted_threshold(test_service, mock_repo, mock_publisher):
    """Test balance depleted event"""
    # Arrange
    ctx = MockContext()
    grant = CreditGrantIn(
        shop_domain="test.myshopify.com",
        amount=5,
        reason="manual
