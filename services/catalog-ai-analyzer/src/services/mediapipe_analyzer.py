# services/catalog-ai-analyzer/src/services/mediapipe_analyzer.py
import time
import cv2
import numpy as np
import mediapipe as mp
from sklearn.cluster import KMeans
from typing import Tuple, List, Optional
from shared.utils.logger import ServiceLogger
from ..config import ServiceConfig
from ..schemas.analysis import PreciseColors

class MediaPipeAnalyzer:
    """MediaPipe-based color extraction from legacy code, adapted for URL-based processing"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self._segmenter = None
    
    async def extract_colors(self, image_bytes: bytes) -> Optional[PreciseColors]:
        """Extract precise colors using MediaPipe segmentation"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                self.logger.error("Failed to decode image")
                return None
            
            # Perform apparel segmentation (from legacy code)
            _, _, _, bound_crop, bound_mask = self._segment_apparel(image)
            
            if bound_crop is None or bound_mask is None:
                self.logger.warning("No apparel detected in image")
                return PreciseColors(
                    rgb_values=[],
                    color_count=0,
                    extraction_method="mediapipe_lab_kmeans"
                )
            
            # Extract color palette using LAB color space (from legacy)
            dominant_colors = self._extract_apparel_palette_lab(
                mask=bound_mask,
                image=bound_crop,
                n_colors=self.config.default_colors,
                sample_size=self.config.sample_size,
                min_chroma=self.config.min_chroma
            )
            
            return PreciseColors(
                rgb_values=dominant_colors,
                color_count=len(dominant_colors),
                extraction_method="mediapipe_lab_kmeans"
            )
            
        except Exception as e:
            self.logger.error(f"MediaPipe color extraction failed: {e}")
            return None
    
    def _get_segmenter(self):
        """Create ImageSegmenter once - from legacy code"""
        if self._segmenter is not None:
            return self._segmenter
        
        from mediapipe.tasks.python.core.base_options import BaseOptions
        from mediapipe.tasks.python.vision.image_segmenter import (
            ImageSegmenter,
            ImageSegmenterOptions,
            _RunningMode,
        )
        
        opts = ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=str(self.config.model_path)),
            running_mode=_RunningMode.IMAGE,
            output_category_mask=True,
        )
        self._segmenter = ImageSegmenter.create_from_options(opts)
        return self._segmenter
    
    def _segment_apparel(self, image: np.ndarray) -> Tuple:
        """Run MediaPipe segmentation - from legacy code"""
        segmenter = self._get_segmenter()
        
        # Wrap NumPy BGR in mp.Image
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        
        # Run segmentation
        result = segmenter.segment(mp_img)
        class_mask = result.category_mask.numpy_view()
        
        # Build binary apparel mask (class 4 = clothes/apparel)
        apparel_mask = np.where(class_mask == 4, 255, 0).astype(np.uint8)
        
        # Colored visualization mask
        coloured_mask = self._make_colour_mask(class_mask)
        
        # Raw crop
        apparel_crop = cv2.bitwise_and(image, image, mask=apparel_mask)
        
        # Find tight bounding box
        ys, xs = np.where(apparel_mask == 255)
        if xs.size == 0 or ys.size == 0:
            return coloured_mask, apparel_mask, None, None, None
        
        x0, x1 = xs.min(), xs.max() + 1
        y0, y1 = ys.min(), ys.max() + 1
        
        bound_crop = apparel_crop[y0:y1, x0:x1]
        bound_mask = apparel_mask[y0:y1, x0:x1]
        
        return coloured_mask, apparel_mask, apparel_crop, bound_crop, bound_mask
    
    def _make_colour_mask(self, segment_mask: np.ndarray):
        """Create colored visualization mask - from legacy code"""
        lut = np.zeros((256, 1, 3), dtype=np.uint8)
        lut[0] = (0, 0, 0)      # bg
        lut[1] = (255, 255, 0)  # hair
        lut[2] = (255, 0, 0)    # body-skin
        lut[3] = (0, 0, 255)    # face-skin
        lut[4] = (0, 255, 0)    # apparel/clothes
        lut[5] = (255, 0, 255)  # other
        return cv2.applyColorMap(segment_mask, lut)
    
    def _extract_apparel_palette_lab(
        self,
        mask: np.ndarray,
        image: np.ndarray,
        n_colors: int = 5,
        sample_size: int = 20000,
        min_chroma: float = 5.0,
    ) -> List[List[int]]:
        """Extract color palette using LAB color space - from legacy code"""
        # Get apparel pixels
        coords = np.where(mask == 255)
        pixels = image[coords]
        
        if len(pixels) == 0:
            return []
        
        # Sample if too many pixels
        if len(pixels) > sample_size:
            idx = np.random.choice(len(pixels), sample_size, replace=False)
            pixels = pixels[idx]
        
        # Convert BGR→RGB→Lab
        pixels_rgb = pixels[:, ::-1]
        pixels_lab = cv2.cvtColor(
            pixels_rgb.reshape(-1, 1, 3), 
            cv2.COLOR_RGB2LAB
        ).reshape(-1, 3)
        
        # K-Means clustering in Lab space
        km = KMeans(n_clusters=n_colors * 2, n_init=8, random_state=0)
        labels = km.fit_predict(pixels_lab)
        centers_lab = km.cluster_centers_
        
        # Compute counts & chroma, filter low-chroma
        counts = np.bincount(labels)
        chroma = np.linalg.norm(centers_lab[:, 1:], axis=1)
        keep = [i for i in np.argsort(-counts) if chroma[i] >= min_chroma]
        
        # Take top n_colors
        chosen = keep[:n_colors]
        palette_rgb = []
        for i in chosen:
            lab = np.uint8(centers_lab[i].reshape(1, 1, 3))
            rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB).reshape(3,)
            palette_rgb.append([int(c) for c in rgb])
        
        return palette_rgb