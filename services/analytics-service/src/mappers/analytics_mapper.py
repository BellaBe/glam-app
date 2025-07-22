from shared.mappers.crud import CRUDMapper
from ..models.analytics import (
    UsageAnalytics, OrderAnalytics, LifecycleTrialAnalytics,
    UsagePattern, PredictionModel, EngagementMetric, ShopifyAnalytics,
    AlertRule, AlertHistory, PlatformMetrics
)
from ..schemas.analytics import (
    UsageAnalyticsIn, UsageAnalyticsOut,
    OrderAnalyticsOut, LifecycleTrialAnalyticsOut,
    UsagePatternOut, PredictionModelIn, PredictionModelOut,
    EngagementMetricOut, ShopifyAnalyticsOut,
    AlertRuleIn, AlertRulePatch, AlertRuleOut,
    AlertHistoryPatch, AlertHistoryOut,
    PlatformMetricsOut
)

class UsageAnalyticsMapper(CRUDMapper[UsageAnalytics, UsageAnalyticsIn, None, UsageAnalyticsOut]):
    """CRUD mapper for UsageAnalytics"""
    model_cls = UsageAnalytics
    out_schema = UsageAnalyticsOut

class OrderAnalyticsMapper(CRUDMapper[OrderAnalytics, None, None, OrderAnalyticsOut]):
    """CRUD mapper for OrderAnalytics"""
    model_cls = OrderAnalytics
    out_schema = OrderAnalyticsOut

class LifecycleTrialAnalyticsMapper(CRUDMapper[LifecycleTrialAnalytics, None, None, LifecycleTrialAnalyticsOut]):
    """CRUD mapper for LifecycleTrialAnalytics"""
    model_cls = LifecycleTrialAnalytics
    out_schema = LifecycleTrialAnalyticsOut

class UsagePatternMapper(CRUDMapper[UsagePattern, None, None, UsagePatternOut]):
    """CRUD mapper for UsagePattern"""
    model_cls = UsagePattern
    out_schema = UsagePatternOut

class PredictionModelMapper(CRUDMapper[PredictionModel, PredictionModelIn, None, PredictionModelOut]):
    """CRUD mapper for PredictionModel"""
    model_cls = PredictionModel
    out_schema = PredictionModelOut

class EngagementMetricMapper(CRUDMapper[EngagementMetric, None, None, EngagementMetricOut]):
    """CRUD mapper for EngagementMetric"""
    model_cls = EngagementMetric
    out_schema = EngagementMetricOut

class ShopifyAnalyticsMapper(CRUDMapper[ShopifyAnalytics, None, None, ShopifyAnalyticsOut]):
    """CRUD mapper for ShopifyAnalytics"""
    model_cls = ShopifyAnalytics
    out_schema = ShopifyAnalyticsOut

class AlertRuleMapper(CRUDMapper[AlertRule, AlertRuleIn, AlertRulePatch, AlertRuleOut]):
    """CRUD mapper for AlertRule"""
    model_cls = AlertRule
    out_schema = AlertRuleOut

class AlertHistoryMapper(CRUDMapper[AlertHistory, None, AlertHistoryPatch, AlertHistoryOut]):
    """CRUD mapper for AlertHistory"""
    model_cls = AlertHistory
    out_schema = AlertHistoryOut

class PlatformMetricsMapper(CRUDMapper[PlatformMetrics, None, None, PlatformMetricsOut]):
    """CRUD mapper for PlatformMetrics"""
    model_cls = PlatformMetrics
    out_schema = PlatformMetricsOut


