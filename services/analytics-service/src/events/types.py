class AnalyticsEvents:
    """Event type constants for analytics"""
    # Predictive alerts
    CHURN_DETECTED = "analytics.churn.detected.v1"
    CREDIT_FORECAST = "analytics.credits.forecast.v1"
    
    # Usage intelligence
    USAGE_ANOMALY = "analytics.usage.anomaly.v1"
    MILESTONE_REACHED = "analytics.milestone.reached.v1"
    
    # Pattern detection
    PATTERN_DETECTED = "analytics.pattern.detected.v1"
    ENGAGEMENT_CHANGE = "analytics.engagement.changed.v1"
    
    # Alert events
    ALERT_TRIGGERED = "analytics.alert.triggered.v1"
    ALERT_RESOLVED = "analytics.alert.resolved.v1"


