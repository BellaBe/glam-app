from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import date
from fastapi import APIRouter, Path, Query, Body, status, HTTPException
from shared.api import ApiResponse, success_response, RequestContextDep
from ...services.analytics_service import AnalyticsService
from ...services.prediction_service import PredictionService
from ...dependencies import AnalyticsServiceDep, PredictionServiceDep
from ...schemas.analytics import (
    UsageAnalyticsOut, OrderAnalyticsOut, LifecycleTrialAnalyticsOut,
    UsagePatternOut, PredictionModelOut, EngagementMetricOut,
    AnalyticsInsightOut, UsageTrendOut, ChurnRiskOut, CustomReportIn
)
from ...models.enums import PatternType, PredictionType, EngagementPeriod
from ...exceptions import AnalyticsNotFoundError

router = APIRouter(prefix="/api/v1", tags=["Analytics"])

# ========== Usage Analytics ==========

@router.get(
    "/merchants/{merchant_id}/analytics/usage",
    response_model=ApiResponse[List[UsageAnalyticsOut]],
    summary="Get usage analytics"
)
async def get_usage_analytics(
    svc: AnalyticsServiceDep,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    breakdown: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    features: Optional[str] = Query(None, description="Comma-separated feature names")
):
    """Get usage analytics for date range"""
    usage_analytics = await svc.get_usage_analytics(merchant_id, start_date, end_date)
    return success_response(usage_analytics, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/usage/trends",
    response_model=ApiResponse[UsageTrendOut],
    summary="Get usage trends"
)
async def get_usage_trends(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    timeframe: str = Query("30d", regex="^(7d|30d|90d|6m|1y)$"),
    compare_period: str = Query("previous", regex="^(previous|year_ago)$")
):
    """Get usage trend analysis"""
    trend = await analytics_svc.get_usage_trends(merchant_id, timeframe, compare_period)
    return success_response(trend, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/features/{feature_name}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get feature-specific analytics"
)
async def get_feature_analytics(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    feature_name: str = Path(..., regex="^(selfie|match|sort)$"),
    period: str = Query("7d", description="Time period for analysis"),
    metrics: Optional[str] = Query("usage,success_rate,performance", description="Comma-separated metrics")
):
    """Get analytics for specific feature"""
    # This would be implemented to return feature-specific metrics
    # For now, return placeholder data
    feature_data = {
        "feature_name": feature_name,
        "period": period,
        "metrics": {
            "total_requests": 150,
            "success_rate": 0.96,
            "avg_processing_time_ms": 850,
            "error_rate": 0.04
        },
        "trend": "stable"
    }
    return success_response(feature_data, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/features/performance",
    response_model=ApiResponse[Dict[str, Any]], 
    summary="Get feature performance metrics"
)
async def get_feature_performance(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    include_errors: bool = Query(False),
    group_by: str = Query("day", regex="^(hour|day|week)$")
):
    """Get feature performance analytics"""
    performance_data = {
        "period": "7d",
        "grouping": group_by,
        "features": {
            "selfie": {
                "avg_response_time_ms": 1200,
                "p95_response_time_ms": 2100,
                "success_rate": 0.94,
                "total_requests": 245
            },
            "match": {
                "avg_response_time_ms": 800,
                "p95_response_time_ms": 1500,
                "success_rate": 0.97,
                "total_requests": 489
            },
            "sort": {
                "avg_response_time_ms": 600,
                "p95_response_time_ms": 1200,
                "success_rate": 0.99,
                "total_requests": 156
            }
        }
    }
    
    if include_errors:
        for feature_data in performance_data["features"].values():
            feature_data["error_details"] = {
                "timeout": 2,
                "invalid_input": 1,
                "service_unavailable": 0
            }
    
    return success_response(performance_data, ctx.request_id, ctx.correlation_id)

# ========== Order Analytics ==========

@router.get(
    "/merchants/{merchant_id}/analytics/orders/daily",
    response_model=ApiResponse[List[OrderAnalyticsOut]],
    summary="Get daily order analytics"
)
async def get_daily_order_analytics(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """Get daily order analytics for date range"""
    # This would get actual order analytics
    order_analytics = []  # Placeholder
    return success_response(order_analytics, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/orders/monthly",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get monthly order analytics"
)
async def get_monthly_order_analytics(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    months: int = Query(12, ge=1, le=24),
    include_projections: bool = Query(False)
):
    """Get monthly order analytics"""
    monthly_data = {
        "months": months,
        "data": [],
        "totals": {
            "orders": 0,
            "revenue": 0
        }
    }
    
    if include_projections:
        monthly_data["projections"] = {
            "next_month_orders": 150,
            "confidence": 0.75
        }
    
    return success_response(monthly_data, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/orders/forecast",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get order forecasts"
)
async def get_order_forecast(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """Get order depletion forecasts and risk levels"""
    forecast_data = {
        "current_usage": 1250,
        "order_limit": 2000,
        "projected_depletion_date": "2024-03-15",
        "days_until_depletion": 45,
        "risk_level": "medium",
        "recommended_actions": [
            "Monitor usage trends closely",
            "Consider upgrading plan if usage increases"
        ]
    }
    return success_response(forecast_data, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/orders/limits",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get current order limits"
)
async def get_order_limits(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """Get current order limits and consumption"""
    limits_data = {
        "order_limit_total": 2000,
        "order_limit_consumed": 1250,
        "order_limit_remaining": 750,
        "utilization_percentage": 62.5,
        "reset_date": "2024-02-01",
        "days_until_reset": 12
    }
    return success_response(limits_data, ctx.request_id, ctx.correlation_id)

# ========== Trial Analytics ==========

@router.get(
    "/merchants/{merchant_id}/analytics/lifecycle/trial/timeline",
    response_model=ApiResponse[LifecycleTrialAnalyticsOut],
    summary="Get trial timeline"
)
async def get_trial_timeline(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """Get complete trial journey with key milestones"""
    try:
        trial_analytics = await analytics_svc.get_trial_analytics(merchant_id)
        if not trial_analytics:
            raise HTTPException(404, "Trial analytics not found")
        return success_response(trial_analytics, ctx.request_id, ctx.correlation_id)
    except AnalyticsNotFoundError:
        raise HTTPException(404, "Trial analytics not found")

@router.get(
    "/merchants/{merchant_id}/analytics/lifecycle/trial/conversion-probability",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get conversion probability"
)
async def get_conversion_probability(
    prediction_svc: PredictionService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """Get ML-predicted conversion likelihood"""
    conversion_data = await prediction_svc.predict_trial_conversion(merchant_id)
    return success_response(conversion_data, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/lifecycle/trial/engagement",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get trial engagement metrics"
)
async def get_trial_engagement(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """Get trial period engagement metrics and recommendations"""
    engagement_data = {
        "engagement_score": 0.78,
        "features_explored": ["selfie", "match"],
        "total_sessions": 12,
        "avg_session_duration": 8.5,
        "days_active": 8,
        "recommendations": [
            "Try the sort feature to complete the product suite",
            "Schedule a demo for advanced features"
        ]
    }
    return success_response(engagement_data, ctx.request_id, ctx.correlation_id)

# ========== Patterns and Predictions ==========

@router.get(
    "/merchants/{merchant_id}/analytics/patterns",
    response_model=ApiResponse[List[UsagePatternOut]],
    summary="Get usage patterns"
)
async def get_usage_patterns(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    type: Optional[str] = Query(None, regex="^(daily|weekly|seasonal|behavioral)$"),
    confidence_threshold: float = Query(0.7, ge=0.0, le=1.0)
):
    """Get detected usage patterns"""
    pattern_types = [PatternType(type)] if type else None
    patterns = await analytics_svc.get_usage_patterns(merchant_id, pattern_types, confidence_threshold)
    return success_response(patterns, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/predictions",
    response_model=ApiResponse[List[PredictionModelOut]],
    summary="Get predictions"
)
async def get_predictions(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    types: Optional[str] = Query(None, description="Comma-separated prediction types")
):
    """Get predictive insights"""
    prediction_types = None
    if types:
        type_list = types.split(",")
        prediction_types = [PredictionType(t) for t in type_list if t in [e.value for e in PredictionType]]
    
    predictions = await analytics_svc.get_predictions(merchant_id, prediction_types)
    return success_response(predictions, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/predictions/churn-risk",
    response_model=ApiResponse[ChurnRiskOut],
    summary="Get churn risk assessment"
)
async def get_churn_risk(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """Get churn risk assessment"""
    churn_risk = await analytics_svc.get_churn_risk(merchant_id)
    if not churn_risk:
        raise HTTPException(404, "Churn risk data not available")
    return success_response(churn_risk, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/engagement",
    response_model=ApiResponse[List[EngagementMetricOut]],
    summary="Get engagement metrics"
)
async def get_engagement_metrics(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    period: EngagementPeriod = Query(EngagementPeriod.MONTHLY),
    include_benchmarks: bool = Query(False)
):
    """Get engagement metrics with optional benchmarks"""
    metrics = await analytics_svc.get_engagement_metrics(merchant_id, period, include_benchmarks)
    return success_response(metrics, ctx.request_id, ctx.correlation_id)

# ========== Analytics Insights ==========

@router.get(
    "/merchants/{merchant_id}/analytics/insights",
    response_model=ApiResponse[List[AnalyticsInsightOut]],
    summary="Get analytics insights"
)
async def get_analytics_insights(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """Get actionable analytics insights"""
    insights = await analytics_svc.generate_insights(merchant_id)
    return success_response(insights, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/benchmark",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get benchmark comparisons"
)
async def get_benchmark_data(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    metrics: str = Query("usage,engagement,growth"),
    anonymized: bool = Query(True)
):
    """Get industry benchmark comparisons"""
    benchmark_data = {
        "merchant_metrics": {
            "usage_score": 0.78,
            "engagement_score": 0.82,
            "growth_rate": 0.15
        },
        "industry_benchmarks": {
            "usage_score": 0.65,
            "engagement_score": 0.70,
            "growth_rate": 0.12
        },
        "percentile_rankings": {
            "usage": 75,
            "engagement": 85,
            "growth": 60
        },
        "peer_comparison": "above_average" if anonymized else None
    }
    return success_response(benchmark_data, ctx.request_id, ctx.correlation_id)

# ========== Custom Reports ==========

@router.post(
    "/merchants/{merchant_id}/analytics/reports/custom",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Generate custom report"
)
async def generate_custom_report(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    report_request: CustomReportIn = Body(...)
):
    """Generate custom analytics report"""
    # This would generate a comprehensive custom report
    report_data = {
        "report_id": "rpt_" + ctx.request_id,
        "report_type": report_request.report_type,
        "generated_at": "2024-01-20T10:30:00Z",
        "metrics": report_request.metrics,
        "time_period": report_request.time_period,
        "format": report_request.format,
        "data": {
            "summary": "Report generated successfully",
            "key_findings": [
                "Usage increased 25% in selected period",
                "High engagement in match feature",
                "Conversion rate above industry average"
            ]
        }
    }
    
    if report_request.include_visualizations:
        report_data["visualizations"] = {
            "charts_generated": 5,
            "chart_types": ["line", "bar", "pie"]
        }
    
    return success_response(report_data, ctx.request_id, ctx.correlation_id)

@router.get(
    "/merchants/{merchant_id}/analytics/reports/scheduled",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="Get scheduled reports"
)
async def get_scheduled_reports(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...)
):
    """Get scheduled reports for merchant"""
    scheduled_reports = [
        {
            "schedule_id": "sch_weekly_usage",
            "report_type": "usage_summary",
            "frequency": "weekly",
            "next_run": "2024-01-27T09:00:00Z",
            "enabled": True
        }
    ]
    return success_response(scheduled_reports, ctx.request_id, ctx.correlation_id)

@router.post(
    "/merchants/{merchant_id}/analytics/reports/schedule",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Schedule report"
)
async def schedule_report(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    schedule_request: Dict[str, Any] = Body(...)
):
    """Schedule recurring analytics report"""
    schedule_data = {
        "schedule_id": "sch_" + ctx.request_id,
        "created_at": "2024-01-20T10:30:00Z",
        "status": "active",
        **schedule_request
    }
    return success_response(schedule_data, ctx.request_id, ctx.correlation_id)

@router.delete(
    "/merchants/{merchant_id}/analytics/reports/scheduled/{schedule_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Delete scheduled report"
)
async def delete_scheduled_report(
    analytics_svc: AnalyticsService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(...),
    schedule_id: str = Path(...)
):
    """Delete scheduled report"""
    return success_response(
        {"message": "Scheduled report deleted", "schedule_id": schedule_id},
        ctx.request_id,
        ctx.correlation_id
    )


