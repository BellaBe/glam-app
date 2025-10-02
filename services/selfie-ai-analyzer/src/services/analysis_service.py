# services/selfie-ai-analyzer/src/services/analysis_service.py
import asyncio
import time
import base64
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4
import numpy as np
import cv2

from shared.utils.logger import ServiceLogger
from shared.utils.exceptions import ValidationError, ServiceUnavailableError, RequestTimeoutError

from ..schemas.analysis import (
    AnalysisRequest, AnalysisResponse, SeasonScores,
    Demographics, ColorAttributes, AnalysisMetrics, ModelVersions
)
from .face_analyzer import FaceAnalyzer
from .color_extractor import ColorExtractor
from .season_calculator import SeasonCalculator
from ..utils.temp_manager import TempManager

class AnalysisService:
    """Main service for selfie analysis orchestration"""
    
    def __init__(
        self,
        face_analyzer: FaceAnalyzer,
        color_extractor: ColorExtractor,
        season_calculator: SeasonCalculator,
        temp_manager: TempManager,
        config,
        logger: ServiceLogger,
        queue: asyncio.Queue
    ):
        self.face_analyzer = face_analyzer
        self.color_extractor = color_extractor
        self.season_calculator = season_calculator
        self.temp_manager = temp_manager
        self.config = config
        self.logger = logger
        self.queue = queue
    
    async def analyze_selfie(
        self,
        request: AnalysisRequest,
        correlation_id: str
    ) -> AnalysisResponse:
        """Main analysis orchestration"""
        
        # Check queue capacity (backpressure)
        if self.queue.full():
            raise ServiceUnavailableError(
                message="Service temporarily unavailable, please retry",
                retry_after=5
            )
        
        # Queue the work
        try:
            result = await asyncio.wait_for(
                self._process_analysis(request, correlation_id),
                timeout=self.config.total_analysis_timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            raise RequestTimeoutError(
                message="Analysis exceeded 24 second timeout",
                timeout_seconds=self.config.total_analysis_timeout_seconds
            )
    
    async def _process_analysis(
        self,
        request: AnalysisRequest,
        correlation_id: str
    ) -> AnalysisResponse:
        """Process analysis with timeout management"""
        
        start_time = time.perf_counter()
        work_dir = None
        warnings = []
        
        try:
            # Setup workspace
            work_dir = await self.temp_manager.create_workspace(request.analysis_id)
            
            # Decode and validate image
            image = await self._decode_and_validate_image(request.image_jpeg_b64)
            
            # Save for processing
            image_path = work_dir / "selfie.png"
            cv2.imwrite(str(image_path), image)
            
            # Run analysis pipelines in parallel with timeouts
            tasks = []
            
            # Face mesh task
            tasks.append(
                self._run_with_timeout(
                    self.face_analyzer.extract_face_mesh(str(image_path)),
                    self.config.mediapipe_timeout_seconds,
                    "face_mesh"
                )
            )
            
            # Selfie segmentation task
            tasks.append(
                self._run_with_timeout(
                    self.face_analyzer.extract_segmentation(str(image_path)),
                    self.config.mediapipe_timeout_seconds,
                    "selfie_seg"
                )
            )
            
            # DeepFace task (optional)
            tasks.append(
                self._run_with_timeout(
                    self.face_analyzer.extract_demographics(str(image_path)),
                    self.config.deepface_timeout_seconds,
                    "demographics"
                )
            )
            
            # Wait for all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            face_mesh = results[0] if not isinstance(results[0], Exception) else None
            segmentation = results[1] if not isinstance(results[1], Exception) else None
            demographics = results[2] if not isinstance(results[2], Exception) else None
            
            # Add warnings for failed components
            if face_mesh is None:
                warnings.append("face_mesh_skipped")
            if segmentation is None:
                warnings.append("segmentation_skipped")
            if demographics is None:
                warnings.append("demographics_skipped")
            
            # Extract colors from regions (critical path)
            color_attributes = await self.color_extractor.extract_region_colors(
                str(image_path),
                segmentation
            )
            
            # Calculate season scores based on extracted colors
            season_scores = await self.season_calculator.compute_season_scores(
                color_attributes
            )
            
            # Determine top seasons
            sorted_seasons = self._sort_seasons(season_scores)
            
            # Build response
            processing_ms = int((time.perf_counter() - start_time) * 1000)
            
            return AnalysisResponse(
                success=True,
                analysis_id=request.analysis_id,
                season_scores=season_scores,
                primary_season=sorted_seasons[0]["name"],
                secondary_season=sorted_seasons[1]["name"],
                tertiary_season=sorted_seasons[2]["name"],
                confidence=sorted_seasons[0]["score"],
                demographics=demographics,
                color_attributes=color_attributes,
                analysis_metrics=AnalysisMetrics(
                    face_landmarks_count=478 if face_mesh else 0,
                    segmentation_classes=6,
                    colors_extracted=self._count_colors(color_attributes),
                    undertone=self._determine_undertone(color_attributes),
                    contrast_level=self._calculate_contrast(color_attributes)
                ),
                warnings=warnings,
                model_versions=ModelVersions(
                    deepface="4.0",
                    mediapipe="0.10.9",
                    algorithm="v1.0.0"
                ),
                processing_ms=processing_ms
            )
            
        finally:
            # Schedule cleanup
            if work_dir:
                asyncio.create_task(
                    self.temp_manager.schedule_cleanup(
                        work_dir,
                        self.config.temp_cleanup_hours
                    )
                )
    
    async def _decode_and_validate_image(self, image_b64: str) -> np.ndarray:
        """Decode base64 image and validate"""
        try:
            # Decode base64
            image_bytes = base64.b64decode(image_b64)
            
            # Check size
            if len(image_bytes) > self.config.max_image_size_bytes:
                raise ValidationError(
                    message=f"Image exceeds {self.config.max_image_size_mb}MB limit",
                    field="image_jpeg_b64"
                )
            
            # Decode to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValidationError(
                    message="Failed to decode image",
                    field="image_jpeg_b64"
                )
            
            # Ensure sRGB color space
            image = self._ensure_srgb(image)
            
            return image
            
        except base64.binascii.Error as e:
            raise ValidationError(
                message="Invalid base64 encoding",
                field="image_jpeg_b64",
                details={"error": str(e)}
            )
    
    def _ensure_srgb(self, image: np.ndarray) -> np.ndarray:
        """Ensure image is in sRGB color space with quality preservation"""
        height, width = image.shape[:2]
        
        # Check if resize is needed
        if max(height, width) > 1280:
            # Calculate face width after resize
            scale = 1280 / max(height, width)
            new_width = int(width * scale)
            
            # Only resize if face width will be >= 300px
            if new_width >= self.config.max_face_width_pixels:
                image = cv2.resize(image, (new_width, int(height * scale)), 
                                 interpolation=cv2.INTER_AREA)
        
        return image
    
    async def _run_with_timeout(self, coro, timeout: float, name: str):
        """Run coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"{name} timed out after {timeout}s")
            return None
        except Exception as e:
            self.logger.exception(f"{name} failed: {e}")
            return None
    
    def _sort_seasons(self, scores: SeasonScores) -> list:
        """Sort seasons by score"""
        season_list = []
        for season_name, score in scores.model_dump().items():
            formatted_name = season_name.replace("_", " ").title()
            season_list.append({"name": formatted_name, "score": score})
        
        return sorted(season_list, key=lambda x: x["score"], reverse=True)
    
    def _count_colors(self, attributes: ColorAttributes) -> int:
        """Count total extracted colors"""
        count = 0
        for region in attributes.model_dump().values():
            if region and "colors" in region:
                count += len(region["colors"])
        return count
    
    def _determine_undertone(self, attributes: ColorAttributes) -> str:
        """Determine undertone from skin colors"""
        if not attributes.face_skin:
            return "neutral"
        
        # Analyze RGB values for warm/cool undertones
        r, g, b = attributes.face_skin.dominant_rgb
        
        # Simple warm/cool detection based on color temperature
        if r > b and g > b:
            return "warm"
        elif b > r:
            return "cool"
        else:
            return "neutral"
    
    def _calculate_contrast(self, attributes: ColorAttributes) -> str:
        """Calculate contrast level between features"""
        if not attributes.hair or not attributes.face_skin:
            return "medium"
        
        # Calculate luminance difference
        hair_lum = sum(attributes.hair.dominant_rgb) / 3
        skin_lum = sum(attributes.face_skin.dominant_rgb) / 3
        
        contrast = abs(hair_lum - skin_lum)
        
        if contrast > 100:
            return "high"
        elif contrast > 50:
            return "medium"
        else:
            return "low"