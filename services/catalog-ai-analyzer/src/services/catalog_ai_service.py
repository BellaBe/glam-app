# services/catalog-ai-analyzer/src/services/catalog_ai_service.py
import asyncio
import time
from typing import Optional, Dict
from uuid import UUID
import httpx
from shared.utils.logger import ServiceLogger
from ..config import ServiceConfig
from ..schemas.analysis import (
    AnalysisItem, ItemAnalysisResult, AnalysisMetadata,
    PreciseColors
)
from .mediapipe_analyzer import MediaPipeAnalyzer
from .openai_analyzer import OpenAIAnalyzer

from ..utils.image_downloader import ImageDownloader
from ..exceptions import (
    ImageDownloadError,
    AnalysisTimeoutError,
    BothAnalyzersFailedError,
    MissingProductIdentifiersError,
)

class CatalogAIService:
    """Main orchestrator for catalog AI analysis"""
    
    def __init__(
        self,
        config: ServiceConfig,
        mediapipe: MediaPipeAnalyzer,
        openai: OpenAIAnalyzer,
        logger: ServiceLogger
    ):
        self.config = config
        self.mediapipe = mediapipe
        self.openai = openai
        self.logger = logger
        
        # Use the image downloader utility
        self.image_downloader = ImageDownloader(
            timeout=config.image_download_timeout,
            max_retries=3,
            logger=logger
        )
    
    async def analyze_single_item(
        self,
        merchant_id: UUID,
        correlation_id: str,
        item: AnalysisItem
    ) -> ItemAnalysisResult:
        """Analyze a single catalog item with proper error handling"""
        start_time = time.perf_counter()
        processing_times = {
            "download_ms": 0,
            "color_extraction_ms": 0,
            "ai_analysis_ms": 0,
            "total_ms": 0
        }
        
        try:
            # Validate required IDs
            if not item.product_id or not item.variant_id:
                raise MissingProductIdentifiersError(
                    item_id=str(item.item_id)
                )
            
            # Download image using the utility
            download_start = time.perf_counter()
            try:
                image_bytes = await self.image_downloader.download(item.image_url)
            except Exception as e:
                raise ImageDownloadError(
                    f"Failed to download image: {str(e)}",
                    url=item.image_url
                )
            processing_times["download_ms"] = int((time.perf_counter() - download_start) * 1000)
            
            # Run parallel analysis with timeout
            try:
                color_task = self._extract_colors_safe(image_bytes)
                ai_task = self._analyze_attributes_safe(image_bytes)
                
                color_result, ai_result = await asyncio.wait_for(
                    asyncio.gather(color_task, ai_task),
                    timeout=self.config.analysis_timeout_per_item
                )
            except asyncio.TimeoutError:
                raise AnalysisTimeoutError(
                    f"Analysis timeout after {self.config.analysis_timeout_per_item}s",
                    timeout_seconds=self.config.analysis_timeout_per_item,
                    item_id=str(item.item_id)
                )
            
            # Check if both failed
            if color_result is None and ai_result is None:
                raise BothAnalyzersFailedError(
                    item_id=str(item.item_id),
                    product_id=item.product_id,
                    variant_id=item.variant_id
                )
            
            # Calculate timings
            processing_times["total_ms"] = int((time.perf_counter() - start_time) * 1000)
            
            # Determine status
            status = self._determine_status(color_result, ai_result)
            
            return ItemAnalysisResult(
                merchant_id=merchant_id,
                item_id=item.item_id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                correlation_id=correlation_id,
                status=status,
                category=ai_result.get("category") if ai_result else None,
                subcategory=ai_result.get("subcategory") if ai_result else None,
                description=ai_result.get("description") if ai_result else None,
                gender=ai_result.get("gender") if ai_result else None,
                attributes=ai_result.get("attributes") if ai_result else None,
                precise_colors=color_result,
                analysis_metadata=AnalysisMetadata(
                    analyzers_used=self._get_analyzers_used(color_result, ai_result),
                    quality_score=self._calculate_quality_score(color_result, ai_result),
                    confidence_score=self._calculate_confidence_score(ai_result),
                    processing_times=processing_times
                ),
                error=None if status != "failed" else "Analysis failed"
            )
            
        except Exception as e:
            self.logger.error(
                f"Item analysis failed: {e}",
                extra={
                    "item_id": str(item.item_id),
                    "product_id": item.product_id,
                    "variant_id": item.variant_id,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            processing_times["total_ms"] = int((time.perf_counter() - start_time) * 1000)
            
            return ItemAnalysisResult(
                merchant_id=merchant_id,
                item_id=item.item_id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                correlation_id=correlation_id,
                status="failed",
                analysis_metadata=AnalysisMetadata(
                    analyzers_used=[],
                    quality_score=0.0,
                    confidence_score=0.0,
                    processing_times=processing_times
                ),
                error=str(e)
            )
    
    async def _extract_colors_safe(self, image_bytes: bytes) -> Optional[PreciseColors]:
        """Safe color extraction that returns None on error"""
        try:
            return await self.mediapipe.extract_colors(image_bytes)
        except Exception as e:
            self.logger.error(f"Color extraction failed: {e}")
            return None
    
    async def _analyze_attributes_safe(self, image_bytes: bytes) -> Optional[Dict]:
        """Safe attribute analysis that returns None on error"""
        try:
            return await self.openai.analyze_attributes(image_bytes)
        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            return None
    
    async def close(self):
        """Cleanup resources"""
        await self.image_downloader.close()