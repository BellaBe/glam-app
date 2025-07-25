# ================================================================================================
# tests/integration/test_events.py
# ================================================================================================
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.events.subscribers import CatalogItemAnalysisSubscriber
from src.events.types import CatalogAnalysisEvents


class TestEventIntegration:

    @pytest.fixture
    def mock_subscriber(self):
        subscriber = CatalogItemAnalysisSubscriber()
        subscriber._dependencies = {}
        return subscriber

    @pytest.fixture
    def mock_service(self):
        service = AsyncMock()
        return service

    @pytest.fixture
    def mock_publisher(self):
        publisher = AsyncMock()
        publisher.publish_event = AsyncMock()
        return publisher

    async def test_catalog_item_analysis_processing(
        self, mock_subscriber, mock_service, mock_publisher, mock_logger
    ):
        """Test processing of catalog item analysis request event"""
        # Setup dependencies
        mock_subscriber._dependencies = {
            "catalog_analysis_service": mock_service,
            "publisher": mock_publisher,
            "logger": mock_logger,
        }

        # Mock successful catalog item analysis
        from src.schemas.catalog_item import CatalogItemAnalysisResult

        mock_result = CatalogItemAnalysisResult(
            status="success",
            colours=[[255, 0, 0], [0, 255, 0]],
            latency_ms=100,
            shop_id="test_shop",
            product_id="test_product",
            variant_id="test_variant",
        )
        mock_service.analyze_catalog_item.return_value = mock_result

        # Create test event
        event = {
            "payload": {
                "shop_id": "test_shop",
                "product_id": "test_product",
                "variant_id": "test_variant",
            },
            "correlation_id": "test-corr-123",
        }

        # Process event
        await mock_subscriber.on_event(event, {})

        # Verify service was called
        mock_service.analyze_catalog_item.assert_called_once()
        request_arg = mock_service.analyze_catalog_item.call_args[0][0]
        assert request_arg.shop_id == "test_shop"

        # Verify success event was published
        mock_publisher.publish_event.assert_called_once_with(
            subject=CatalogAnalysisEvents.ITEM_ANALYSIS_COMPLETED,
            payload=mock_result.model_dump(),
            correlation_id="test-corr-123",
        )
