from enum import Enum

class AlertType(str, Enum):
    """Alert type enumeration"""
    CREDIT_LOW = "credit_low"
    ORDER_LIMIT_LOW = "order_limit_low"
    CHURN_RISK = "churn_risk"
    TRIAL_EXPIRING = "trial_expiring"
    USAGE_SPIKE = "usage_spike"
    ERROR_RATE_HIGH = "error_rate_high"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status enumeration"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"

class PredictionType(str, Enum):
    """Prediction type enumeration"""
    CREDIT_DEPLETION = "credit_depletion"
    CHURN_RISK = "churn_risk"
    TRIAL_CONVERSION = "trial_conversion"
    GROWTH_FORECAST = "growth_forecast"

class PatternType(str, Enum):
    """Usage pattern types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    SEASONAL = "seasonal"
    BEHAVIORAL = "behavioral"

class EngagementPeriod(str, Enum):
    """Engagement metric periods"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class DepletionRiskLevel(str, Enum):
    """Order depletion risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThresholdOperator(str, Enum):
    """Alert threshold operators"""
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_THAN_EQUAL = "<="
    GREATER_THAN_EQUAL = ">="
    EQUAL = "="


