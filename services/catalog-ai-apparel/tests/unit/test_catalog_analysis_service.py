================
# tests/unit/test_catalog_analysis_service.py
================
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from src.services.catalog_analysis_service import CatalogAnalysisService
from src.schemas.catalog_item import CatalogItemAnalysisRequest

@pytest.fixture
def sample_request():
    return CatalogItemAnalysisRequest(
        shop_id="test_shop",
        product_id="test_product", 
        variant_id="test_variant"
    )

@pytest.fixture
def catalog_analysis_service(mock_config, mock_logger):
    """Create catalog analysis service with mocked dependencies"""
    with patch('src.services.catalog_analysis_service.Path') as mock_path:
        mock_path.return_value.is_file.return_value = True
        return CatalogAnalysisService(mock_config, mock_logger)

class TestCatalogAnalysisService:
    
    async def test_analyze_catalog_item_success(self, catalog_analysis_service, sample_request, mock_config):
        """Test successful catalog item analysis processing"""
        # Mock file operations
        with patch('src.services.catalog_analysis_service.Path') as mock_path_cls, \
             patch('cv2.imread') as mock_imread, \
             patch('cv2.imwrite') as mock_imwrite, \
             patch.object(catalog_analysis_service, '_segment_apparel') as mock_segment, \
             patch.object(catalog_analysis_service, '_extract_apparel_palette_lab') as mock_extract:
            
            # Setup mocks
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_cls.return_value = mock_path
            
            mock_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            
            # Mock apparel segmentation results
            mock_segment.return_value = (
                np.zeros((100, 100, 3)),  # coloured_mask
                np.zeros((100, 100)),     # apparel_mask  
                np.zeros((100, 100, 3)),  # apparel_crop
                np.zeros((50, 50, 3)),    # bound_crop
                np.zeros((50, 50))        # bound_mask
            )
            
            # Mock color extraction
            mock_extract.return_value = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]
            
            # Execute
            result = await catalog_analysis_service.analyze_catalog_item(sample_request)
            
            # Verify
            assert result.status == "success"
            assert len(result.colours) == 3
            assert result.latency_ms > 0
            assert result.shop_id == sample_request.shop_id
            
            # Verify file operations were called
            mock_imread.assert_called_once()
            assert mock_imwrite.call_count == 3  # Three output files
    
    async def test_analyze_catalog_item_file_not_found(self, catalog_analysis_service, sample_request):
        """Test handling of missing catalog item image"""
        with patch('src.services.catalog_analysis_service.Path') as mock_path_cls:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path_cls.return_value = mock_path
            
            result = await catalog_analysis_service.analyze_catalog_item(sample_request)
            
            assert result.status == "error"
            assert "not found" in result.error
            assert result.colours is None
    
    async def test_analyze_catalog_item_no_apparel_detected(self, catalog_analysis_service, sample_request):
        """Test handling when no apparel is detected in catalog item"""
        with patch('src.services.catalog_analysis_service.Path') as mock_path_cls, \
             patch('cv2.imread') as mock_imread, \
             patch.object(catalog_analysis_service, '_segment_apparel') as mock_segment:
            
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_cls.return_value = mock_path
            
            mock_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            
            # Mock no apparel detected
            mock_segment.return_value = (
                np.zeros((100, 100, 3)),  # coloured_mask
                np.zeros((100, 100)),     # apparel_mask
                None, None, None          # No apparel found
            )
            
            result = await catalog_analysis_service.analyze_catalog_item(sample_request)
            
            assert result.status == "success"  # Original behavior: success with empty colours
            assert result.colours == []