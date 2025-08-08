import pytest
import uuid7
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.services.webhook_processor import WebhookProcessor
from src.models.enums import WebhookStatus, ShopifyWebhookTopic
from src.schemas.webhook import WebhookEntryOut


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_publisher():
    publisher = AsyncMock()
    return publisher


@pytest.fixture
def test_processor(mock_repo, mock_publisher):
    from shared.utils.logger import create_logger
    from src.config import ServiceConfig
    
    logger = create_logger("test")
    config = MagicMock(spec=ServiceConfig)
    config.webhook_max_retries = 10
    
    return WebhookProcessor(
        config=config,
        repository=mock_repo,
        publisher=mock_publisher,
        logger=logger
    )


@pytest.fixture
def sample_webhook():
    return WebhookEntryOut(
        id=uuid7.uuid7(),
        platform="shopify",
        topic_raw="orders/create",
        topic_enum=ShopifyWebhookTopic.ORDERS_CREATE.value,
        shop_domain="test-shop.myshopify.com",
        webhook_id=str(uuid7.uuid7()),
        api_version="2024-01",
        status=WebhookStatus.RECEIVED.value,
        processing_attempts=0,
        error_message=None,
        received_at=datetime.utcnow(),
        processed_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        payload={
            "id": 123456,
            "total_price": "100.00",
            "currency": "USD",
            "created_at": "2024-01-15T10:00:00Z",
            "line_items": [{"id": 1}, {"id": 2}]
        }
    )


async def test_process_webhook_order_created(test_processor, mock_repo, mock_publisher, sample_webhook):
    """Test processing order created webhook"""
    webhook_id = str(sample_webhook.id)
    correlation_id = str(uuid7.uuid7())
    
    # Setup mocks
    mock_repo.find_by_id.return_value = sample_webhook
    mock_repo.update_status = AsyncMock()
    mock_publisher.order_created = AsyncMock()
    
    # Process webhook
    await test_processor.process_webhook(webhook_id, correlation_id)
    
    # Verify calls
    mock_repo.find_by_id.assert_called_once()
    mock_repo.update_status.assert_any_call(
        sample_webhook.id,
        WebhookStatus.PROCESSING
    )
    
    # Verify event published
    mock_publisher.order_created.assert_called_once_with(
        shop_domain="test-shop.myshopify.com",
        order_id="123456",
        total_price="100.00",
        currency="USD",
        created_at="2024-01-15T10:00:00Z",
        line_items_count=2,
        webhook_id=sample_webhook.webhook_id,
        correlation_id=correlation_id
    )
    
    # Verify marked as processed
    mock_repo.update_status.assert_called_with(
        sample_webhook.id,
        WebhookStatus.PROCESSED,
        processed_at=pytest.Any(datetime)
    )


async def test_process_webhook_app_uninstalled(test_processor, mock_repo, mock_publisher):
    """Test processing app uninstalled webhook"""
    webhook = WebhookEntryOut(
        id=uuid7.uuid7(),
        platform="shopify",
        topic_raw="app/uninstalled",
        topic_enum=ShopifyWebhookTopic.APP_UNINSTALLED.value,
        shop_domain="test-shop.myshopify.com",
        webhook_id=str(uuid7.uuid7()),
        api_version="2024-01",
        status=WebhookStatus.RECEIVED.value,
        processing_attempts=0,
        error_message=None,
        received_at=datetime.utcnow(),
        processed_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        payload={}
    )
    
    correlation_id = str(uuid7.uuid7())
    
    # Setup mocks
    mock_repo.find_by_id.return_value = webhook
    mock_publisher.app_uninstalled = AsyncMock()
    
    # Process webhook
    await test_processor.process_webhook(str(webhook.id), correlation_id)
    
    # Verify event published
    mock_publisher.app_uninstalled.assert_called_once_with(
        shop_domain="test-shop.myshopify.com",
        webhook_id=webhook.webhook_id,
        correlation_id=correlation_id
    )


async def test_process_webhook_not_found(test_processor, mock_repo):
    """Test processing non-existent webhook"""
    webhook_id = str(uuid7.uuid7())
    correlation_id = str(uuid7.uuid7())
    
    # Setup mocks
    mock_repo.find_by_id.return_value = None
    
    # Process webhook - should return without error
    await test_processor.process_webhook(webhook_id, correlation_id)
    
    # Verify no further processing
    mock_repo.update_status.assert_not_called()


async def test_process_webhook_error_handling(test_processor, mock_repo, mock_publisher, sample_webhook):
    """Test error handling during webhook processing"""
    webhook_id = str(sample_webhook.id)
    correlation_id = str(uuid7.uuid7())
    
    # Setup mocks
    mock_repo.find_by_id.return_value = sample_webhook
    mock_repo.increment_attempts.return_value = sample_webhook
    mock_publisher.order_created.side_effect = Exception("Publishing failed")
    
    # Process webhook - should raise
    with pytest.raises(Exception, match="Publishing failed"):
        await test_processor.process_webhook(webhook_id, correlation_id)
    
    # Verify attempts incremented
    mock_repo.increment_attempts.assert_called_once_with(sample_webhook.id)


async def test_process_webhook_max_retries_exceeded(test_processor, mock_repo, mock_publisher):
    """Test webhook failure after max retries"""
    webhook = WebhookEntryOut(
        id=uuid7.uuid7(),
        platform="shopify",
        topic_raw="orders/create",
        topic_enum=ShopifyWebhookTopic.ORDERS_CREATE.value,
        shop_domain="test-shop.myshopify.com",
        webhook_id=str(uuid7.uuid7()),
        api_version="2024-01",
        status=WebhookStatus.PROCESSING.value,
        processing_attempts=9,  # One below max
        error_message=None,
        received_at=datetime.utcnow(),
        processed_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        payload={"id": 123}
    )
    
    correlation_id = str(uuid7.uuid7())
    
    # Setup mocks
    mock_repo.find_by_id.return_value = webhook
    mock_repo.increment_attempts.return_value = WebhookEntryOut(
        **{**webhook.model_dump(), "processing_attempts": 10}
    )
    mock_publisher.order_created.side_effect = Exception("Publishing failed")
    
    # Process webhook
    with pytest.raises(Exception):
        await test_processor.process_webhook(str(webhook.id), correlation_id)
    
    # Verify marked as failed
    mock_repo.update_status.assert_called_with(
        webhook.id,
        WebhookStatus.FAILED,
        error_message="Publishing failed"
    )


