# services/recommendation-service/tests/integration/test_api.py
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch


@pytest.fixture
async def app():
    """Create test app with mocked dependencies"""
    from src.main import create_application
    return create_application()


@pytest.fixture
async def client(app: FastAPI):
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_recommendation_endpoint(client):
    """Test recommendation creation endpoint"""
    
    with patch("src.dependencies.get_recommendation_service") as mock_svc:
        mock_service = AsyncMock()
        mock_service.create_recommendation.return_value = {
            "match_id": "match_123",
            "total_matches": 1,
            "matches": []
        }
        mock_svc.return_value = mock_service
        
        response = await client.post(
            "/api/v1/recommendations",
            json={
                "analysis_id": "analysis_123",
                "shopper_id": "shopper_456",
                "primary_season": "True Spring",
                "confidence": 0.85,
                "season_scores": {"True Spring": 0.85}
            },
            headers={
                "Authorization": "Bearer test_token",
                "X-Shop-Platform": "shopify",
                "X-Shop-Domain": "test.myshopify.com"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["match_id"] == "match_123"


@pytest.mark.asyncio
async def test_get_match_endpoint(client):
    """Test get match endpoint"""
    
    with patch("src.dependencies.get_recommendation_service") as mock_svc:
        mock_service = AsyncMock()
        mock_service.get_match.return_value = {
            "id": "match_123",
            "merchant_id": "00000000-0000-0000-0000-000000000001",
            "total_matches": 0
        }
        mock_svc.return_value = mock_service
        
        response = await client.get(
            "/api/v1/recommendations/match_123",
            headers={
                "Authorization": "Bearer test_token",
                "X-Shop-Platform": "shopify",
                "X-Shop-Domain": "test.myshopify.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == "match_123"