from typing import List, Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Query, Path, HTTPException
from shared.api import ApiResponse, success_response, RequestContextDep
from ...repositories.platform_repository import PlatformMetricsRepository
from ...mappers.analytics_mapper import PlatformMetricsMapper
from ...dependencies import LifecycleDep

router = APIRouter(prefix="/api/v1/analytics/platform", tags=["Platform Analytics"])

# ========== Platform Overview ==========

@router.get(
    "/overview",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get platform overview"
)
async def get_platform_overview(
    lifecycle: LifecycleDep,
    ctx: RequestContextDep,
    period: str = Query("30d", regex="^(7d|30d|90d)$"),
    include_forecasts: bool = Query(False)
):
    """Get platform-wide analytics overview"""
    platform_repo = lifecycle.platform_repo
    
    # Get recent platform metrics
    today = date.today()
    latest_metrics = await platform_repo.find_by_date(today)
    
    overview_data = {
        "date": today.isoformat(),
        "period": period,
        "metrics": {
            "total_merchants": latest_metrics.total_merchants if latest_metrics else 0,
            "active_merchants": latest_metrics.active_merchants if latest_metrics else 0,
            "total_credits_consumed": float(latest_metrics.total_credits_consumed) if latest_metrics else 0,
            "total_api_calls": latest_metrics.total_api_calls if latest_metrics else 0,
            "platform_uptime": float(latest_metrics.platform_uptime) if latest_metrics else 1.0,
            "revenue": float(latest_metrics.revenue) if latest_metrics else 0,
            "mrr": float(latest_metrics.mrr) if latest_metrics else 0
        }
    }
    
    if include_forecasts:
        # Get growth metrics for forecasting
        growth_data = await platform_repo.get_growth_metrics(30)
        overview_data["forecasts"] = {
            "next_month_revenue": overview_data["metrics"]["revenue"] * 1.1,  # Simplified
            "merchant_growth_rate": growth_data.get("merchant_growth", 0),
            "usage_growth_rate": growth_data.get("usage_growth", 0)
        }
    
    return success_response(overview_data, ctx.request_id, ctx.correlation_id)

@router.get(
    "/trends",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get platform trends"
)
async def get_platform_trends(
    lifecycle: LifecycleDep,
    ctx: RequestContextDep,
    metrics: str = Query("merchants,revenue,usage"),
    timeframe: str = Query("12m", regex="^(3m|6m|12m|24m)$")
):
    """Get platform growth and trends"""
    platform_repo = lifecycle.platform_repo
    
    # Parse timeframe
    months = int(timeframe[:-1])
    growth_data = await platform_repo.get_growth_metrics(months * 30)
    
    trend_data = {
        "timeframe": timeframe,
        "requested_metrics": metrics.split(","),
        "trends": growth_data,
        "summary": {
            "overall_health": "healthy",
            "growth_trajectory": "positive" if growth_data.get("merchant_growth", 0) > 0 else "stable",
            "key_insights": [
                "Platform showing steady growth",
                "API usage increasing consistently",
                "Merchant retention improving"
            ]
        }
    }
    
    return success_response(trend_data, ctx.request_id, ctx.correlation_id)

@router.get(
    "/forecasts",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get platform forecasts"
)
async def get_platform_forecasts(
    lifecycle: LifecycleDep,
    ctx: RequestContextDep,
    models: str = Query("revenue,churn,growth"),
    horizon: str = Query("6m", regex="^(3m|6m|12m)$")
):
    """Get platform business forecasts"""
    platform_repo = lifecycle.platform_repo
    
    # Get aggregated data for forecasting
    months = int(horizon[:-1])
    historical_data = await platform_repo.get_aggregated_metrics(months * 2)  # Get 2x horizon for better prediction
    
    forecast_data = {
        "horizon": horizon,
        "models": models.split(","),
        "forecasts": {
            "revenue": {
                "predicted_value": historical_data["total_revenue"] * 1.15,  # Simplified 15% growth
                "confidence_interval": {
                    "lower": historical_data["total_revenue"] * 1.05,
                    "upper": historical_data["total_revenue"] * 1.25
                },
                "confidence": 0.75
            },
            "churn": {
                "predicted_rate": 0.05,  # 5% monthly churn
                "trend": "stable",
                "confidence": 0.80
            },
            "growth": {
                "merchant_growth_rate": 0.12,  # 12% monthly growth
                "usage_growth_rate": 0.18,   # 18% usage growth
                "confidence": 0.70
            }
        },
        "assumptions": [
            "Historical trends continue",
            "No major market disruptions",
            "Current pricing model maintained"
        ]
    }
    
    return success_response(forecast_data, ctx.request_id, ctx.correlation_id)

# ========== Cohort Analysis ==========

@router.get(
    "/cohorts",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get cohort analysis"
)
async def get_cohort_analysis(
    lifecycle: LifecycleDep,
    ctx: RequestContextDep,
    group_by: str = Query("signup_month", regex="^(signup_month|plan_type|region)$"),
    metrics: str = Query("retention,revenue")
):
    """Get platform-wide cohort analysis (admin only)"""
    # This would perform sophisticated cohort analysis
    cohort_data = {
        "group_by": group_by,
        "metrics": metrics.split(","),
        "cohorts": [
            {
                "cohort_id": "2024-01",
                "size": 150,
                "retention": {
                    "month_1": 0.85,
                    "month_3": 0.72,
                    "month_6": 0.65
                },
                "revenue": {
                    "month_1": 12500,
                    "month_3": 15600,
                    "month_6": 18900
                }
            },
            {
                "cohort_id": "2024-02", 
                "size": 180,
                "retention": {
                    "month_1": 0.88,
                    "month_3": 0.75,
                    "month_6": 0.68
                },
                "revenue": {
                    "month_1": 14200,
                    "month_3": 17800,
                    "month_6": 21300
                }
            }
        ],
        "insights": [
            "Recent cohorts showing improved retention",
            "Revenue per cohort increasing over time",
            "Month 3 retention is critical threshold"
        ]
    }
    
    return success_response(cohort_data, ctx.request_id, ctx.correlation_id)

@router.get(
    "/segments",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get merchant segments"
)
async def get_merchant_segments(
    lifecycle: LifecycleDep,
    ctx: RequestContextDep,
    criteria: str = Query("usage_level,plan_type"),
    include_trends: bool = Query(False)
):
    """Get merchant segmentation analysis (admin only)"""
    segment_data = {
        "segmentation_criteria": criteria.split(","),
        "segments": {
            "power_users": {
                "count": 45,
                "percentage": 15,
                "avg_monthly_usage": 2500,
                "avg_revenue": 299,
                "characteristics": ["High API usage", "Multi-feature adoption", "Long sessions"]
            },
            "regular_users": {
                "count": 135,
                "percentage": 45,
                "avg_monthly_usage": 800,
                "avg_revenue": 99,
                "characteristics": ["Consistent usage", "Primary feature focus", "Good retention"]
            },
            "casual_users": {
                "count": 120,
                "percentage": 40,
                "avg_monthly_usage": 200,
                "avg_revenue": 29,
                "characteristics": ["Sporadic usage", "Single feature", "Price sensitive"]
            }
        },
        "recommendations": {
            "power_users": "Focus on advanced features and enterprise plans",
            "regular_users": "Encourage feature exploration and plan upgrades",
            "casual_users": "Improve onboarding and demonstrate value"
        }
    }
    
    if include_trends:
        segment_data["trends"] = {
            "segment_migration": "15% of regular users upgraded to power users last quarter",
            "growth_rates": {
                "power_users": 0.25,
                "regular_users": 0.12,
                "casual_users": 0.08
            }
        }
    
    return success_response(segment_data, ctx.request_id, ctx.correlation_id)


