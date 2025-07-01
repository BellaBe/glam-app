
# -------------------------------
# shared/errors/selfie.py
# -------------------------------

"""Selfie service specific errors."""

from typing import Optional, List
from .base import NotFoundError, ValidationError


class SelfieNotFoundError(NotFoundError):
    """Selfie not found."""
    
    code = "SELFIE_NOT_FOUND"
    
    def __init__(
        self,
        message: str,
        *,
        selfie_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, resource="selfie", resource_id=selfie_id, **kwargs)
        
        if user_id:
            self.details["user_id"] = user_id


class InvalidImageFormatError(ValidationError):
    """Image format not supported."""
    
    code = "INVALID_IMAGE_FORMAT"
    
    def __init__(
        self,
        message: str,
        *,
        provided_format: Optional[str] = None,
        supported_formats: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if provided_format:
            self.details["provided_format"] = provided_format
        if supported_formats:
            self.details["supported_formats"] = supported_formats


class ImageTooLargeError(ValidationError):
    """Image exceeds size limit."""
    
    code = "IMAGE_TOO_LARGE"
    
    def __init__(
        self,
        message: str,
        *,
        size_bytes: Optional[int] = None,
        max_size_bytes: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if size_bytes:
            self.details["size_bytes"] = size_bytes
        if max_size_bytes:
            self.details["max_size_bytes"] = max_size_bytes


class ImageTooSmallError(ValidationError):
    """Image below minimum dimensions."""
    
    code = "IMAGE_TOO_SMALL"
    
    def __init__(
        self,
        message: str,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if width:
            self.details["width"] = width
        if height:
            self.details["height"] = height
        if min_width:
            self.details["min_width"] = min_width
        if min_height:
            self.details["min_height"] = min_height


class NoFaceDetectedError(ValidationError):
    """No face detected in image."""
    
    code = "NO_FACE_DETECTED"
    
    def __init__(
        self,
        message: str = "No face detected in the image",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class MultipleFacesDetectedError(ValidationError):
    """Multiple faces detected."""
    
    code = "MULTIPLE_FACES_DETECTED"
    
    def __init__(
        self,
        message: str = "Multiple faces detected in the image",
        *,
        face_count: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if face_count:
            self.details["face_count"] = face_count


class PoorImageQualityError(ValidationError):
    """Image quality too low for analysis."""
    
    code = "POOR_IMAGE_QUALITY"
    
    def __init__(
        self,
        message: str = "Image quality too low for analysis",
        *,
        quality_score: Optional[float] = None,
        min_quality_score: Optional[float] = None,
        quality_issues: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if quality_score is not None:
            self.details["quality_score"] = quality_score
        if min_quality_score is not None:
            self.details["min_quality_score"] = min_quality_score
        if quality_issues:
            self.details["quality_issues"] = quality_issues
