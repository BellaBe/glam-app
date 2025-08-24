# services/selfie-service/src/services/image_processor.py
from PIL import Image, ImageCms
import io
import cv2
import numpy as np
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any
from shared.utils.exceptions import ValidationError
from shared.utils.logger import ServiceLogger
from ..config import ServiceConfig

class ImageProcessor:
    """Image validation and processing service"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        
        # Load face detection model
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    async def validate_and_process(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Validate image and prepare for AI analysis.
        Returns processed image data and metrics.
        """
        # Check file size
        if len(image_bytes) > self.config.max_upload_size:
            raise ValidationError(
                message=f"File exceeds {self.config.max_upload_size // 1_048_576}MB limit",
                code="IMAGE_TOO_LARGE"
            )
        
        # Check magic bytes for format
        if not self._validate_format(image_bytes):
            raise ValidationError(
                message="Invalid image format. Supported: JPEG, PNG, WebP",
                code="INVALID_IMAGE_FORMAT"
            )
        
        # Open and validate image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValidationError(
                message="Cannot decode image",
                code="INVALID_IMAGE_FORMAT",
                details={"error": str(e)}
            )
        
        # Convert to sRGB color space
        rgb_image = self._ensure_srgb(image)
        width, height = rgb_image.size
        
        # Check dimensions
        if width < self.config.min_image_dimension or height < self.config.min_image_dimension:
            raise ValidationError(
                message=f"Image too small. Minimum: {self.config.min_image_dimension}x{self.config.min_image_dimension}",
                code="IMAGE_TOO_SMALL",
                details={"width": width, "height": height}
            )
        
        if width * height > self.config.max_image_pixels:
            raise ValidationError(
                message=f"Image exceeds {self.config.max_image_pixels // 1_000_000}MP limit",
                code="IMAGE_TOO_LARGE_DIMENSIONS",
                details={"megapixels": (width * height) / 1_000_000}
            )
        
        # Quality checks on downscaled copy
        quality_image = self._resize_for_quality_check(rgb_image)
        quality_metrics = self._check_quality(quality_image)
        
        # Validate quality metrics
        self._validate_quality(quality_metrics)
        
        # Prepare image for AI analyzer
        analyzer_jpeg = self._prepare_analyzer_image(
            rgb_image,
            face_bbox=quality_metrics['face_bbox']
        )
        
        # Compute deduplication hash
        image_hash = self._compute_hash(
            rgb_image.tobytes(),
            width,
            height
        )
        
        return {
            "width": width,
            "height": height,
            "image_hash": image_hash,
            "analyzer_jpeg_b64": base64.b64encode(analyzer_jpeg).decode(),
            "blur_score": quality_metrics['blur_score'],
            "exposure_score": quality_metrics['exposure_score'],
            "face_area_ratio": quality_metrics['face_area_ratio']
        }
    
    def _validate_format(self, image_bytes: bytes) -> bool:
        """Check magic bytes for supported formats"""
        # JPEG
        if image_bytes[:2] == b'\xff\xd8':
            return True
        # PNG
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return True
        # WebP
        if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return True
        return False
    
    def _ensure_srgb(self, image: Image.Image) -> Image.Image:
        """Convert to sRGB color space"""
        # Apply EXIF rotation
        image = self._apply_exif_rotation(image)
        
        # Convert to RGB mode
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        # Handle ICC profile conversion
        if 'icc_profile' in image.info:
            try:
                input_profile = ImageCms.ImageCmsProfile(
                    io.BytesIO(image.info['icc_profile'])
                )
                srgb_profile = ImageCms.createProfile('sRGB')
                image = ImageCms.profileToProfile(
                    image,
                    input_profile,
                    srgb_profile,
                    renderingIntent=ImageCms.Intent.PERCEPTUAL
                )
            except Exception as e:
                self.logger.warning(f"ICC conversion failed: {e}")
        
        # Ensure RGB (drop alpha)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        return image
    
    def _apply_exif_rotation(self, image: Image.Image) -> Image.Image:
        """Apply EXIF rotation to correct orientation"""
        try:
            exif = image._getexif()
            if exif is not None:
                orientation = exif.get(0x0112)
                if orientation:
                    rotations = {
                        3: 180,
                        6: 270,
                        8: 90
                    }
                    if orientation in rotations:
                        image = image.rotate(rotations[orientation], expand=True)
        except Exception:
            pass
        return image
    
    def _resize_for_quality_check(self, image: Image.Image) -> np.ndarray:
        """Resize image for quality checks (max 1024px)"""
        max_side = 1024
        width, height = image.size
        
        if max(width, height) > max_side:
            if width > height:
                new_width = max_side
                new_height = int(height * max_side / width)
            else:
                new_height = max_side
                new_width = int(width * max_side / height)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to numpy array for OpenCV
        return np.array(image)
    
    def _check_quality(self, image_array: np.ndarray) -> Dict[str, Any]:
        """Run quality checks on image"""
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        # Blur detection (Laplacian)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Exposure check (average luminance)
        exposure_score = np.mean(gray)
        
        # Face detection
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            raise ValidationError(
                message="No face detected in image",
                code="IMAGE_QUALITY_INSUFFICIENT",
                details={"reason": "no_face"}
            )
        
        if len(faces) > 1:
            raise ValidationError(
                message="Multiple faces detected",
                code="IMAGE_QUALITY_INSUFFICIENT",
                details={"reason": "multiple_faces", "count": len(faces)}
            )
        
        # Get face bbox
        x, y, w, h = faces[0]
        face_area = (w * h) / (image_array.shape[0] * image_array.shape[1])
        
        return {
            "blur_score": float(blur_score),
            "exposure_score": float(exposure_score),
            "face_area_ratio": float(face_area),
            "face_bbox": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
        }
    
    def _validate_quality(self, metrics: Dict[str, Any]):
        """Validate quality metrics against thresholds"""
        if metrics['blur_score'] < self.config.min_blur_score:
            raise ValidationError(
                message="Image is too blurry",
                code="IMAGE_QUALITY_INSUFFICIENT",
                details={"reason": "blur", "score": metrics['blur_score']}
            )
        
        if not (self.config.min_exposure <= metrics['exposure_score'] <= self.config.max_exposure):
            raise ValidationError(
                message="Poor image exposure",
                code="IMAGE_QUALITY_INSUFFICIENT",
                details={"reason": "exposure", "score": metrics['exposure_score']}
            )
        
        if metrics['face_area_ratio'] < self.config.min_face_area_ratio:
            raise ValidationError(
                message="Face too small in image",
                code="IMAGE_QUALITY_INSUFFICIENT",
                details={"reason": "face_size", "ratio": metrics['face_area_ratio']}
            )
    
    def _prepare_analyzer_image(self, rgb_image: Image.Image, face_bbox: Dict) -> bytes:
        """Prepare color-accurate JPEG for AI analyzer"""
        # Calculate if face would be too small after resize
        width, height = rgb_image.size
        max_side = max(width, height)
        resize_ratio = min(self.config.analyzer_max_side / max_side, 1.0)
        face_width_after = face_bbox['width'] * resize_ratio
        
        # Skip resize if face would be too small
        if face_width_after < self.config.min_face_width_after_resize:
            analyzer_img = rgb_image
            self.logger.info(f"Skipping resize to preserve face size: {face_bbox['width']}px")
        else:
            analyzer_img = self._resize_max_side(rgb_image, self.config.analyzer_max_side)
        
        # First attempt: High quality with no chroma subsampling
        jpeg_bytes = self._image_to_jpeg(
            analyzer_img,
            quality=self.config.analyzer_quality_high,
            subsampling=0  # 4:4:4 for color accuracy
        )
        
        # If too large, reduce quality (not subsampling)
        if len(jpeg_bytes) > self.config.analyzer_max_size:
            jpeg_bytes = self._image_to_jpeg(
                analyzer_img,
                quality=self.config.analyzer_quality_medium,
                subsampling=0
            )
            self.logger.info(f"Reduced quality to {self.config.analyzer_quality_medium}")
        
        return jpeg_bytes
    
    def _resize_max_side(self, image: Image.Image, max_side: int) -> Image.Image:
        """Resize keeping aspect ratio"""
        width, height = image.size
        if max(width, height) <= max_side:
            return image
        
        if width > height:
            new_width = max_side
            new_height = int(height * max_side / width)
        else:
            new_height = max_side
            new_width = int(width * max_side / height)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _image_to_jpeg(self, image: Image.Image, quality: int, subsampling: int) -> bytes:
        """Convert to JPEG with specified parameters"""
        buffer = io.BytesIO()
        # Clean image (no EXIF/ICC)
        clean_image = Image.new('RGB', image.size)
        clean_image.putdata(list(image.getdata()))
        clean_image.save(
            buffer,
            format='JPEG',
            quality=quality,
            optimize=True,
            subsampling=subsampling,
            progressive=True
        )
        return buffer.getvalue()
    
    def _compute_hash(self, rgb_bytes: bytes, width: int, height: int) -> str:
        """Compute HMAC-SHA256 for deduplication"""
        # Construct message: merchant_id || width || height || rgb_bytes
        # Note: merchant_id will be added by the service layer
        message = f"{width}:{height}:".encode() + rgb_bytes[:1024]  # Sample for performance
        
        return hmac.new(
            self.config.global_dedup_secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()