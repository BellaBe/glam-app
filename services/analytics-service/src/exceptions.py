# services/analytics/src/exceptions.py
"""Analytics service domain-specific exceptions"""

from shared.utils.exceptions import DomainError, ValidationError, InfrastructureError
from typing import Optional, Any

class AnalyticsError(DomainError):
    """Base class for analytics domain errors"""
    code = "ANALYTICS_ERROR"

class MetricsNotFoundError(AnalyticsError):
    """Raised when requested metrics are not available"""
    code = "METRICS_NOT_FOUND"
    status = 404
    
    def __init__(
        self, 
        merchant_id: str,
        metric_type: str,
        period: Optional[str] = None,
        **kwargs
    ):
        message = f"No {metric_type} metrics found for merchant {merchant_id}"
        if period:
            message += f" for period {period}"
        
        super().__init__(
            message,
            details={
                "merchant_id": merchant_id,
                "metric_type": metric_type,
                "period": period
            },
            **kwargs
        )

class AggregationError(AnalyticsError):
    """Raised when aggregation fails"""
    code = "AGGREGATION_ERROR"
    status = 500
    
    def __init__(
        self,
        operation: str,
        reason: str,
        merchant_id: Optional[str] = None,
        **kwargs
    ):
        message = f"Aggregation failed for {operation}: {reason}"
        
        super().__init__(
            message,
            details={
                "operation": operation,
                "reason": reason,
                "merchant_id": merchant_id
            },
            **kwargs
        )

class MetricCalculationError(AnalyticsError):
    """Raised when metric calculation fails"""
    code = "METRIC_CALCULATION_ERROR"
    status = 500
    
    def __init__(
        self,
        metric_name: str,
        reason: str,
        data: Optional[dict] = None,
        **kwargs
    ):
        message = f"Failed to calculate {metric_name}: {reason}"
        
        super().__init__(
            message,
            details={
                "metric_name": metric_name,
                "reason": reason,
                "data": data
            },
            **kwargs
        )

class DataConsistencyError(AnalyticsError):
    """Raised when data consistency issues are detected"""
    code = "DATA_CONSISTENCY_ERROR"
    status = 409
    
    def __init__(
        self,
        entity: str,
        expected: Any,
        actual: Any,
        **kwargs
    ):
        message = f"Data consistency error in {entity}"
        
        super().__init__(
            message,
            details={
                "entity": entity,
                "expected": expected,
                "actual": actual
            },
            **kwargs
        )

class InvalidPeriodError(ValidationError):
    """Raised when an invalid time period is requested"""
    code = "INVALID_PERIOD"
    status = 400
    
    def __init__(
        self,
        period: str,
        valid_periods: list[str],
        **kwargs
    ):
        super().__init__(
            f"Invalid period '{period}'. Valid periods are: {', '.join(valid_periods)}",
            field="period",
            value=period,
            **kwargs
        )

class InsufficientDataError(AnalyticsError):
    """Raised when there's not enough data for meaningful analytics"""
    code = "INSUFFICIENT_DATA"
    status = 200  # Return success but with explanation
    
    def __init__(
        self,
        metric_type: str,
        minimum_required: int,
        actual_count: int,
        **kwargs
    ):
        message = f"Insufficient data for {metric_type} analytics"
        
        super().__init__(
            message,
            details={
                "metric_type": metric_type,
                "minimum_required": minimum_required,
                "actual_count": actual_count
            },
            **kwargs
        )