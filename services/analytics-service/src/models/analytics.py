from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Date, DateTime, Numeric, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from uuid import UUID, uuid4
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any, Dict, List
from shared.database.base import Base, TimestampedMixin, MerchantMixin
from .enums import (
    AlertType, AlertSeverity, AlertStatus, PredictionType, 
    PatternType, EngagementPeriod, DepletionRiskLevel, ThresholdOperator
)

class UsageAnalytics(Base, TimestampedMixin, MerchantMixin):
    """Daily, per-merchant usage roll-up"""
    __tablename__ = "usage_analytics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Feature usage breakdown (JSON)
    feature_usage: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Credit and usage metrics
    total_credits_consumed: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    unique_users: Mapped[int] = mapped_column(Integer, default=0)
    api_calls: Mapped[int] = mapped_column(Integer, default=0)
    peak_hour: Mapped[Optional[int]] = mapped_column(Integer)  # 0-23
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Performance metrics
    average_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    p95_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)

class OrderAnalytics(Base, TimestampedMixin, MerchantMixin):
    """Daily order-limit tracking for legacy compatibility"""
    __tablename__ = "order_analytics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Order tracking
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    daily_average: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    monthly_average: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    
    # Order limits
    order_limit_total: Mapped[int] = mapped_column(Integer, default=0)
    order_limit_consumed: Mapped[int] = mapped_column(Integer, default=0)
    order_limit_remaining: Mapped[int] = mapped_column(Integer, default=0)
    
    # Projections
    projected_depletion_date: Mapped[Optional[date]] = mapped_column(Date)
    days_until_depletion: Mapped[Optional[int]] = mapped_column(Integer)
    depletion_risk_level: Mapped[DepletionRiskLevel] = mapped_column(String(20), default=DepletionRiskLevel.LOW)
    
    # Alert tracking
    threshold_warnings_sent: Mapped[dict] = mapped_column(JSON, default=list)
    
    # Trends
    weekly_trend: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    monthly_trend: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

class LifecycleTrialAnalytics(Base, TimestampedMixin, MerchantMixin):
    """Lifecycle data for merchants in trial period"""
    __tablename__ = "lifecycle_trial_analytics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Trial lifecycle
    trial_start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    trial_end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    trial_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    trial_extension_count: Mapped[int] = mapped_column(Integer, default=0)
    total_extension_days: Mapped[int] = mapped_column(Integer, default=0)
    
    # Conversion tracking
    converted: Mapped[bool] = mapped_column(Boolean, default=False)
    conversion_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    conversion_plan_id: Mapped[Optional[str]] = mapped_column(String(100))
    time_to_conversion_days: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Engagement
    trial_engagement_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    features_used_during_trial: Mapped[list] = mapped_column(JSON, default=list)
    days_until_first_usage: Mapped[int] = mapped_column(Integer, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_session_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    
    # ML predictions
    conversion_probability: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    conversion_factors: Mapped[Optional[dict]] = mapped_column(JSON)

class UsagePattern(Base, TimestampedMixin, MerchantMixin):
    """Discovered behavioral or temporal patterns"""
    __tablename__ = "usage_patterns"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pattern_type: Mapped[PatternType] = mapped_column(String(20), nullable=False)
    pattern_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    pattern_strength: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_validated: Mapped[Optional[datetime]] = mapped_column(DateTime)

class PredictionModel(Base, TimestampedMixin, MerchantMixin):
    """Point-in-time prediction outputs"""
    __tablename__ = "prediction_models"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    prediction_type: Mapped[PredictionType] = mapped_column(String(30), nullable=False)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False)
    prediction_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    
    # Confidence and metadata
    confidence_interval: Mapped[Optional[dict]] = mapped_column(JSON)
    factors: Mapped[Optional[dict]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Validation
    accuracy_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    actual_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    prediction_error: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

class EngagementMetric(Base, TimestampedMixin, MerchantMixin):
    """Rolling activity metrics"""
    __tablename__ = "engagement_metrics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    period: Mapped[EngagementPeriod] = mapped_column(String(10), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Activity metrics
    active_days: Mapped[int] = mapped_column(Integer, default=0)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    average_session_duration_minutes: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    
    # Feature engagement
    feature_adoption: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Retention and loyalty
    user_retention: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    api_engagement: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    feature_stickiness: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    
    # Behavioral indicators
    power_user_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    exploration_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    satisfaction_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    
    calculated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class ShopifyAnalytics(Base, TimestampedMixin, MerchantMixin):
    """Daily snapshot of Shopify integration health"""
    __tablename__ = "shopify_analytics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    shop_id: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Integration health
    webhook_events_processed: Mapped[int] = mapped_column(Integer, default=0)
    webhook_events_failed: Mapped[int] = mapped_column(Integer, default=0)
    api_calls_made: Mapped[int] = mapped_column(Integer, default=0)
    api_calls_failed: Mapped[int] = mapped_column(Integer, default=0)
    api_rate_limit_hits: Mapped[int] = mapped_column(Integer, default=0)
    
    # App engagement
    app_session_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    app_page_views: Mapped[int] = mapped_column(Integer, default=0)
    subscription_changes: Mapped[int] = mapped_column(Integer, default=0)
    billing_events: Mapped[int] = mapped_column(Integer, default=0)
    
    # Store characteristics
    store_plan: Mapped[Optional[str]] = mapped_column(String(50))
    store_timezone: Mapped[Optional[str]] = mapped_column(String(50))
    store_country: Mapped[Optional[str]] = mapped_column(String(10))
    store_primary_currency: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Installation and lifecycle
    installation_source: Mapped[Optional[str]] = mapped_column(String(100))
    days_since_installation: Mapped[Optional[int]] = mapped_column(Integer)
    app_version: Mapped[Optional[str]] = mapped_column(String(20))

class AlertRule(Base, TimestampedMixin):
    """Configurable alert rules"""
    __tablename__ = "alert_rules"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    merchant_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))  # None for platform-wide
    
    # Rule definition
    alert_type: Mapped[AlertType] = mapped_column(String(30), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Threshold configuration
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    threshold_operator: Mapped[ThresholdOperator] = mapped_column(String(5), nullable=False)
    comparison_period: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Alert behavior
    severity: Mapped[AlertSeverity] = mapped_column(String(10), nullable=False)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=60)
    max_alerts_per_day: Mapped[int] = mapped_column(Integer, default=10)
    
    # Notification configuration
    notification_channels: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Rule status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered: Mapped[Optional[datetime]] = mapped_column(DateTime)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))

class AlertHistory(Base, TimestampedMixin, MerchantMixin):
    """Historical record of triggered alerts"""
    __tablename__ = "alert_history"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_rule_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    
    # Alert details
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    
    # Context and resolution
    alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    context_data: Mapped[Optional[dict]] = mapped_column(JSON)
    status: Mapped[AlertStatus] = mapped_column(String(20), default=AlertStatus.ACTIVE)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(100))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Notification tracking
    notifications_sent: Mapped[Optional[dict]] = mapped_column(JSON)
    notification_failures: Mapped[Optional[dict]] = mapped_column(JSON)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class PlatformMetrics(Base, TimestampedMixin):
    """Daily platform-wide metrics"""
    __tablename__ = "platform_metrics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    
    # Merchant metrics
    total_merchants: Mapped[int] = mapped_column(Integer, default=0)
    active_merchants: Mapped[int] = mapped_column(Integer, default=0)
    new_merchants: Mapped[int] = mapped_column(Integer, default=0)
    churned_merchants: Mapped[int] = mapped_column(Integer, default=0)
    trial_merchants: Mapped[int] = mapped_column(Integer, default=0)
    
    # Usage metrics
    total_credits_consumed: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total_api_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_feature_usage: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Financial metrics
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    mrr: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    arr: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # Segmented metrics
    by_plan: Mapped[dict] = mapped_column(JSON, default=dict)
    by_feature: Mapped[dict] = mapped_column(JSON, default=dict)
    by_region: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Performance metrics
    platform_uptime: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.0)
    average_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))


