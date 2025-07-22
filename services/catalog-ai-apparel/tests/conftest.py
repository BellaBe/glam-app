# ================================================================================================
# tests/conftest.py
# ================================================================================================
import pytest
import pytest_asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session", autouse=True)
def setup_test_config():
    """Set up test configuration"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "true"
    
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture(scope="session")
async def redis_container():
    """Redis test container"""
    with RedisContainer("redis:7-alpine") as redis:
        os.environ["REDIS_URL"] = redis.get_connection_url()
        yield redis

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = MagicMock()
    config.service_name = "catalog-analysis"
    config.model_path = "tests/fixtures/mock_model.tflite"
    config.products_base_path = "tests/fixtures/products"
    config.analysis_dir_name = "analysis"
    config.default_colors = 5
    config.sample_size = 1000
    config.min_chroma = 5.0
    config.debug = True
    return config

@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    return logger