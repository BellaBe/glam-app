# services/selfie-ai-analyzer/src/services/face_analyzer.py
import asyncio
import threading
import mediapipe as mp
import numpy as np
from typing import Optional, Dict, Any
from deepface import DeepFace
from shared.utils.logger import ServiceLogger
from ..schemas.analysis import Demographics

class FaceAnalyzer:
    """Face analysis using MediaPipe and DeepFace"""
    
    def __init__(self, config, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Initialize MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
        
        # Global lock for DeepFace (thread safety)
        self.deepface_lock = threading.Lock() if config.deepface_thread_lock else None
    
    async def extract_face_mesh(self, image_path: str) -> Optional[Dict]:
        """Extract 478 face landmarks using MediaPipe"""
        try:
            return await asyncio.to_thread(self._run_face_mesh, image_path)
        except Exception as e:
            self.logger.error(f"Face mesh extraction failed: {e}")
            return None
    
    def _run_face_mesh(self, image_path: str) -> Dict:
        """Run face mesh in thread"""
        import cv2
        
        with self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        ) as face_mesh:
            
            image = cv2.imread(image_path)
            results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            if not results.multi_face_landmarks:
                return None
            
            landmarks = results.multi_face_landmarks[0]
            return {
                "landmarks": [[lm.x, lm.y, lm.z] for lm in landmarks.landmark],
                "count": len(landmarks.landmark)
            }
    
    async def extract_segmentation(self, image_path: str) -> Optional[Dict]:
        """Extract selfie segmentation using MediaPipe"""
        try:
            return await asyncio.to_thread(self._run_segmentation, image_path)
        except Exception as e:
            self.logger.error(f"Segmentation extraction failed: {e}")
            return None
    
    def _run_segmentation(self, image_path: str) -> Dict:
        """Run segmentation in thread"""
        import cv2
        
        with self.mp_selfie_segmentation.SelfieSegmentation(
            model_selection=1  # 0 or 1, 1 is more accurate
        ) as selfie_segmentation:
            
            image = cv2.imread(image_path)
            results = selfie_segmentation.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Get segmentation mask
            condition = results.segmentation_mask > 0.5
            
            return {
                "mask": results.segmentation_mask,
                "segments": self._extract_segments(results.segmentation_mask)
            }
    
    def _extract_segments(self, mask: np.ndarray) -> Dict:
        """Extract different segments from mask"""
        # MediaPipe provides confidence values for different regions
        # We can threshold to get hair, face, background etc.
        return {
            "background": mask < 0.1,
            "hair": (mask > 0.1) & (mask < 0.3),
            "face": (mask > 0.3) & (mask < 0.7),
            "body": mask > 0.7
        }
    
    async def extract_demographics(self, image_path: str) -> Optional[Demographics]:
        """Extract demographics using DeepFace with lock"""
        try:
            return await asyncio.to_thread(self._run_deepface, image_path)
        except Exception as e:
            self.logger.error(f"Demographics extraction failed: {e}")
            return None
    
    def _run_deepface(self, image_path: str) -> Demographics:
        """Run DeepFace in thread with optional lock"""
        
        # Use lock if configured for thread safety
        if self.deepface_lock:
            with self.deepface_lock:
                result = self._deepface_analyze(image_path)
        else:
            result = self._deepface_analyze(image_path)
        
        if not result:
            return None
        
        # Map DeepFace results to our schema
        return Demographics(
            age=int(result.get("age", 0)),
            gender="f" if result.get("gender", {}).get("Woman", 0) > 50 else "m",
            race=result.get("dominant_race", "unknown").lower()
        )
    
    def _deepface_analyze(self, image_path: str) -> Dict:
        """Actual DeepFace analysis"""
        try:
            results = DeepFace.analyze(
                img_path=image_path,
                actions=["age", "gender", "race"],
                enforce_detection=True,
                detector_backend=self.config.deepface_backend
            )
            
            # DeepFace returns a list if multiple faces
            if isinstance(results, list):
                return results[0] if results else None
            return results
            
        except Exception as e:
            self.logger.warning(f"DeepFace analysis failed: {e}")
            return None