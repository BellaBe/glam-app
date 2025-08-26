# services/selfie-service/src/exceptions.py
from shared.utils.exceptions import DomainError, ValidationError


class ImageValidationError(ValidationError):
    """Image-specific validation errors"""

    pass


class ImageQualityError(ValidationError):
    """Image quality issues"""

    def __init__(self, message: str, reason: str, **kwargs):
        super().__init__(message, **kwargs)
        self.details["reason"] = reason


class ImageFormatError(ValidationError):
    """Invalid image format"""

    code = "INVALID_IMAGE_FORMAT"
    status = 400


class ImageSizeError(ValidationError):
    """Image size issues"""

    pass


class ImageTooLargeError(ImageSizeError):
    """Image file too large"""

    code = "IMAGE_TOO_LARGE"
    status = 413


class ImageTooSmallError(ImageSizeError):
    """Image dimensions too small"""

    code = "IMAGE_TOO_SMALL"
    status = 422


class ImageDimensionError(ImageSizeError):
    """Image pixel count too large"""

    code = "IMAGE_TOO_LARGE_DIMENSIONS"
    status = 422


class FaceDetectionError(ValidationError):
    """Face detection issues"""

    code = "IMAGE_QUALITY_INSUFFICIENT"
    status = 422


class NoFaceError(FaceDetectionError):
    """No face detected"""

    def __init__(self):
        super().__init__(message="No face detected in image", details={"reason": "no_face"})


class MultipleFacesError(FaceDetectionError):
    """Multiple faces detected"""

    def __init__(self, count: int):
        super().__init__(message="Multiple faces detected", details={"reason": "multiple_faces", "count": count})


class AnalysisError(DomainError):
    """Analysis processing errors"""

    code = "ANALYSIS_FAILED"
    status = 500


class AnalysisTimeoutError(AnalysisError):
    """Analysis timed out"""

    code = "PROCESSING_TIMEOUT"
    status = 504
