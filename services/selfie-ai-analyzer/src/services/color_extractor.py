# services/selfie-ai-analyzer/src/services/color_extractor.py
import cv2
import numpy as np
from typing import Optional, Dict, List
from sklearn.cluster import KMeans
from shared.utils.logger import ServiceLogger
from ..schemas.analysis import ColorAttributes, ColorInfo

class ColorExtractor:
    """Extract colors from different regions of the image"""
    
    def __init__(self, logger: ServiceLogger):
        self.logger = logger
        self.n_colors = 3  # Number of dominant colors to extract per region
    
    async def extract_region_colors(
        self, 
        image_path: str,
        segmentation: Optional[Dict] = None
    ) -> ColorAttributes:
        """Extract colors from different regions"""
        
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Extract colors from different regions
        hair_colors = None
        skin_colors = None
        left_iris_colors = None
        right_iris_colors = None
        
        if segmentation and "segments" in segmentation:
            segments = segmentation["segments"]
            
            # Extract hair colors
            if "hair" in segments:
                hair_region = image_rgb[segments["hair"]]
                if len(hair_region) > 0:
                    hair_colors = self._extract_dominant_colors(hair_region)
            
            # Extract skin colors
            if "face" in segments:
                face_region = image_rgb[segments["face"]]
                if len(face_region) > 0:
                    skin_colors = self._extract_dominant_colors(face_region)
        else:
            # Fallback: use simple region detection
            h, w = image_rgb.shape[:2]
            
            # Top region for hair
            hair_region = image_rgb[0:h//3, w//4:3*w//4]
            hair_colors = self._extract_dominant_colors(hair_region.reshape(-1, 3))
            
            # Middle region for face
            face_region = image_rgb[h//3:2*h//3, w//4:3*w//4]
            skin_colors = self._extract_dominant_colors(face_region.reshape(-1, 3))
        
        # Extract eye colors (simplified - would need eye detection)
        # For now, use a central face region
        eye_region = image_rgb[2*h//5:3*h//5, w//3:2*w//3]
        eye_colors = self._extract_dominant_colors(eye_region.reshape(-1, 3))
        
        # Build response
        return ColorAttributes(
            hair=self._to_color_info(hair_colors) if hair_colors else None,
            face_skin=self._to_color_info(skin_colors) if skin_colors else None,
            left_iris=self._to_color_info(eye_colors) if eye_colors else None,
            right_iris=self._to_color_info(eye_colors) if eye_colors else None
        )
    
    def _extract_dominant_colors(self, pixels: np.ndarray) -> List[List[int]]:
        """Extract dominant colors using K-means clustering"""
        
        if len(pixels) < self.n_colors:
            return []
        
        # Reshape if needed
        if len(pixels.shape) == 3:
            pixels = pixels.reshape(-1, 3)
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=self.n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get cluster centers (dominant colors)
        colors = kmeans.cluster_centers_.astype(int)
        
        # Sort by frequency
        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        sorted_indices = np.argsort(counts)[::-1]
        
        return [colors[i].tolist() for i in sorted_indices]
    
    def _to_color_info(self, colors: List[List[int]]) -> ColorInfo:
        """Convert color list to ColorInfo"""
        if not colors:
            return None
        
        return ColorInfo(
            dominant_rgb=colors[0],
            colors=colors
        )