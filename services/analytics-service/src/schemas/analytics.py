from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Any
from ..models.enums import (
    AlertType, AlertSeverity, AlertStatus, PredictionType,
    PatternType, EngagementPeriod, DepletionRiskLevel, ThresholdOperator
)

# ========== INPUT DTOs ==========

class UsageAnalyticsIn(BaseModel):
    """Input DTO for creating usage analytics"""
    date: date
    feature_usage: Dict[str, Any] = Field(default_factory=dict)
    total_credits_consumed: Decimal = Field(default=0, ge=0)
    unique_users: int = Field(default=0, ge=0)
    api_calls: int = Field(default=0, ge=0)
    peak_hour: Optional[int] = Field(None, ge=0, le=23)
    error_count: int = Field(default=0, ge=0)
    average_response_time_ms: Optional[int] = Field(None, ge=0)
    p95_response_time_ms: Optional[int] = Field(None, ge=0)
    
    model_config = ConfigDict(extra="forbid")

class AlertRuleIn(BaseModel):
    """Input DTO for creating alert rule"""
    alert_type: AlertType
    rule_name: str = Field(..., max_length=200, min_length=1)
    rule_description: Optional[str] = Field(None, max_length=1000)
    metric_name: str = Field(..., max_length=100, min_length=1)
    threshold_value: Decimal
    threshold_operator: ThresholdOperator
    comparison_period: Optional[str] = Field(None, max_length=10)
    severity: AlertSeverity
    cooldown_minutes: int = Field(60, ge=1, le=1440)
    max_alerts_per_day: int = Field(10, ge=1, le=100)
    notification_channels: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(extra="forbid")

class PredictionModelIn(BaseModel):
    """Input DTO for creating prediction"""
    prediction_type: PredictionType
    prediction_date: date
    prediction_value: Decimal
    confidence_interval: Optional[Dict[str, Any]] = None
    factors: Optional[Dict[str, Any]] = None
    model_version: str = Field(..., max_length=50)
    
    model_config = ConfigDict(extra="forbid")

# ========== PATCH DTOs ==========

class AlertRulePatch(BaseModel):
    """Patch DTO for updating alert rule"""
    rule_name: Optional[str] = Field(None, max_length=200, min_length=1)
    rule_description: Optional[str] = Field(None, max_length=1000)
    threshold_value: Optional[Decimal] = None
    threshold_operator: Optional[ThresholdOperator] = None
    severity: Optional[AlertSeverity] = None
    cooldown_minutes: Optional[int] = Field(None, ge=1, le=1440)
    max_alerts_per_day: Optional[int] = Field(None, ge=1, le=100)
    notification_channels: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(extra="forbid")

class AlertHistoryPatch(BaseModel):
    """Patch DTO for updating alert history"""
    status: Optional[AlertStatus] = None
    resolved_by: Optional[str] = Field(None, max_length=100)
    resolution_notes: Optional[str] = Field(None, max_length=1000)
    
    model_config = ConfigDict(extra="forbid")

# ========== OUTPUT DTOs ==========

class UsageAnalyticsOut(BaseModel):
    """Output DTO for usage analytics"""
    id: UUID
    merchant_id: UUID
    merchant_domain: str
    date: date
    feature_usage: Dict[str, Any]
    total_credits_consumed: Decimal
    unique_users: int
    api_calls: int
    peak_hour: Optional[int]
    error_count: int
    average_response_time_ms: Optional[int]
    p95_response_time_ms: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OrderAnalyticsOut(BaseModel):
    """Output DTO for order analytics"""
    id: UUID
    merchant_id: UUID
    merchant_domain: str
    date: date
    total_orders: int
    daily_average: Optional[Decimal]
    monthly_average: Optional[Decimal]
    order_limit_total: int
    order_limit_consumed: int
    order_limit_remaining: int
    projected_depletion_date: Optional[date]
    days_until_depletion: Optional[int]
    depletion_risk_level: DepletionRiskLevel
    threshold_warnings_sent: List[Dict[str, Any]]
    weekly_trend: Optional[Decimal]
    monthly_trend: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LifecycleTrialAnalyticsOut(BaseModel):
    """Output DTO for trial analytics"""
    id: UUID
    merchant_id: UUID
    merchant_domain: str
    trial_start_date: datetime
    trial_end_date: datetime
    trial_duration_days: int
    trial_extension_count: int
    total_extension_days: int
    converted: bool
    conversion_date: Optional[datetime]
    conversion_plan_id: Optional[str]
    time_to_conversion_days: Optional[int]
    trial_engagement_score: Decimal
    features_used_during_trial: List[str]
    days_until_first_usage: int
    total_sessions: int
    total_session_duration_minutes: int
    conversion_probability: Decimal
    conversion_factors: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UsagePatternOut(BaseModel):
    """Output DTO for usage pattern"""
    id: UUID
    merchant_id: UUID
    merchant_domain: str
    pattern_type: PatternType
    pattern_data: Dict[str, Any]
    confidence_score: Decimal
    pattern_strength: Decimal
    sample_size: int
    detected_at: datetime
    valid_until: Optional[datetime]
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PredictionModelOut(BaseModel):
    """Output DTO for prediction model"""
    id: UUID
    merchant_id: UUID
    merchant_domain: str
    prediction_type: PredictionType
    prediction_date: date
    prediction_value: Decimal
    confidence_interval: Optional[Dict[str, Any]]
    factors: Optional[Dict[str, Any]]
    model_version: str
    accuracy_score: Optional[Decimal]
    actual_value: Optional[Decimal]
    prediction_error: Optional[Decimal]
    validated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EngagementMetricOut(BaseModel):
    """Output DTO for engagement metric"""
    id: UUID
    merchant_id: UUID
    merchant_domain: str
    period: EngagementPeriod
    period_start: datetime
    period_end: datetime
    active_days: int
    total_sessions: int
    average_session_duration_minutes: Decimal
    feature_adoption: Dict[str, Any]
    user_retention: Decimal
    api_engagement: Decimal
    feature_stickiness: Decimal
    power_user_score: Decimal
    exploration_score: Decimal
    satisfaction_score: Decimal
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ShopifyAnalyticsOut(BaseModel):
    """Output DTO for Shopify analytics"""
    id: UUID
    merchant_id: UUID
    merchant_domain: str
    shop_id: str
    date: date
    webhook_events_processed: int
    webhook_events_failed: int
    api_calls_made: int
    api_calls_failed: int
    api_rate_limit_hits: int
    app_session_duration_minutes: int
    app_page_views: int
    subscription_changes: int
    billing_events: int
    store_plan: Optional[str]
    store_timezone: Optional[str]
    store_country: Optional[str]
    store_primary_currency: Optional[str]
    installation_source: Optional[str]
    days_since_installation: Optional[int]
    app_version: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AlertRuleOut(BaseModel):
    """Output DTO for alert rule"""
    id: UUID
    merchant_id: Optional[UUID]
    alert_type: AlertType
    rule_name: str
    rule_description: Optional[str]
    metric_name: str
    threshold_value: Decimal
    threshold_operator: ThresholdOperator
    comparison_period: Optional[str]
    severity: AlertSeverity
    cooldown_minutes: int
    max_alerts_per_day: int
    notification_channels: Dict[str, Any]
    is_active: bool
    last_triggered: Optional[datetime]
    trigger_count: int
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AlertHistoryOut(BaseModel):
    """Output DTO for alert history"""
    id: UUID
    alert_rule_id: UUID
    merchant_id: UUID
    merchant_domain: str
    alert_type: str
    severity: str
    metric_name: str
    metric_value: Decimal
    threshold_value: Decimal
    alert_message: str
    context_data: Optional[Dict[str, Any]]
    status: AlertStatus
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    notifications_sent: Optional[Dict[str, Any]]
    notification_failures: Optional[Dict[str, Any]]
    triggered_at: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PlatformMetricsOut(BaseModel):
    """Output DTO for platform metrics"""
    id: UUID
    date: date
    total_merchants: int
    active_merchants: int
    new_merchants: int
    churned_merchants: int
    trial_merchants: int
    total_credits_consumed: Decimal
    total_api_calls: int
    total_feature_usage: Dict[str, Any]
    revenue: Decimal
    mrr: Decimal
    arr: Decimal
    by_plan: Dict[str, Any]
    by_feature: Dict[str, Any]
    by_region: Dict[str, Any]
    platform_uptime: Decimal
    average_response_time_ms: Optional[int]
    error_rate: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ========== SPECIALIZED DTOs ==========

class AnalyticsInsightOut(BaseModel):
    """Analytics insight response"""
    insight_type: str
    title: str
    description: str
    metrics: Dict[str, Any]
    recommendations: List[str]
    confidence: Decimal
    created_at: datetime
    
    model_config = ConfigDict(extra="allow")

class UsageTrendOut(BaseModel):
    """Usage trend analysis"""
    period: str
    trend_direction: str  # "up", "down", "stable"
    percentage_change: Decimal
    current_value: Decimal
    previous_value: Decimal
    data_points: List[Dict[str, Any]]
    
    model_config = ConfigDict(extra="allow")

class ChurnRiskOut(BaseModel):
    """Churn risk assessment"""
    merchant_id: UUID
    risk_score: Decimal
    risk_level: str
    factors: List[Dict[str, Any]]
    recommended_actions: List[str]
    predicted_churn_date: Optional[date]
    confidence: Decimal
    
    model_config = ConfigDict(from_attributes=True)

class CustomReportIn(BaseModel):
    """Custom report request"""
    report_type: str = Field(..., regex="^(comprehensive|summary|focused)$")
    metrics: List[str]
    time_period: str
    format: str = Field("json", regex="^(json|pdf|csv)$")
    include_visualizations: bool = False
    filters: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


