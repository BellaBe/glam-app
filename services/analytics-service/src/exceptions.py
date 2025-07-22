from shared.exceptions import ServiceError, NotFoundError

class AnalyticsError(ServiceError):
    """Base analytics service error"""
    pass

class AnalyticsNotFoundError(NotFoundError):
    """Analytics resource not found error"""
    pass

class AlertError(ServiceError):
    """Alert system error"""
    pass

class AlertNotFoundError(NotFoundError):
    """Alert not found error"""
    pass

class PredictionError(ServiceError):
    """Prediction service error"""
    pass

class PatternDetectionError(ServiceError):
    """Pattern detection error"""
    pass


