# services/recommendation-service/tests/unit/test_recommendation_service.py
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from src.schemas.recommendation import RecommendationRequest
from src.services.recommendation_service import RecommendationService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_season_client():
    return AsyncMock()


@pytest.fixture
def test_service(mock_repo, mock_season_client):
    from shared.utils import create_logger

    logger = create_logger("test")
    return RecommendationService(repository=mock_repo, season_client=mock_season_client, min_score=0.7, logger=logger)


@pytest.mark.asyncio
async def test_create_recommendation_success(test_service, mock_repo, mock_season_client):
    # Arrange
    request = RecommendationRequest(
        analysis_id="analysis_123",
        shopper_id="shopper_456",
        primary_season="True Spring",
        confidence=0.85,
        season_scores={"True Spring": 0.85},
    )

    mock_season_client.get_compatible_items.return_value = [
        {
            "item_id": "item_1",
            "product_id": "prod_1",
            "variant_id": "var_1",
            "score": 0.92,
            "matching_season": "True Spring",
        }
    ]

    mock_repo.create_match.return_value = MagicMock(id="match_123")

    # Act
    result = await test_service.create_recommendation(
        merchant_id=UUID("00000000-0000-0000-0000-000000000001"),
        platform_name="shopify",
        domain="test.myshopify.com",
        request=request,
        correlation_id="corr_123",
    )

    # Assert
    assert result.match_id == "match_123"
    assert result.total_matches == 1
    assert len(result.matches) == 1
    assert result.matches[0].score == 0.92


@pytest.mark.asyncio
async def test_create_recommendation_invalid_season(test_service):
    # Arrange
    request = RecommendationRequest(
        analysis_id="analysis_123",
        shopper_id="shopper_456",
        primary_season="Invalid Season",
        confidence=0.85,
        season_scores={},
    )

    # Act & Assert
    from shared.utils.exceptions import ValidationError

    with pytest.raises(ValidationError) as exc:
        await test_service.create_recommendation(
            merchant_id=UUID("00000000-0000-0000-0000-000000000001"),
            platform_name="shopify",
            domain="test.myshopify.com",
            request=request,
            correlation_id="corr_123",
        )

    assert "Invalid primary season" in str(exc.value)
