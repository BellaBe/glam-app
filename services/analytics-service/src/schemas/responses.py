# services/analytics/src/schemas/responses.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TodayMetrics(BaseModel):
    """Today's snapshot metrics"""
    shoppers: int
    matches: int
    credits_used: int
    match_rate: float
    drop_off_rate: float
    peak_hour: Optional[int] = None
    avg_analysis_time: int

class Last30DaysMetrics(BaseModel):
    """Last 30 days aggregated metrics"""
    total_shoppers: int
    total_matches: int
    unique_shoppers: int
    returning_shoppers: int
    return_rate: float
    analysis_frequency: float
    avg_products_per_match: float
    zero_match_rate: float
    credits_consumed: int
    credits_remaining: int
    days_until_depletion: Optional[int] = None
    catalog_freshness: Optional[int] = None

class CatalogMetrics(BaseModel):
    """Catalog performance metrics"""
    total_products: int
    analyzed_products: int
    analysis_coverage: float
    products_never_matched: int

class PerformanceMetrics(BaseModel):
    """System performance metrics"""
    analysis_success_rate: float
    avg_processing_time: int
    failed_analyses_today: int

class TrendsMetrics(BaseModel):
    """Trend indicators"""
    shopper_growth: str
    match_rate: float
    daily_avg_credits: float

class SummaryData(BaseModel):
    """Complete summary response data"""
    today: TodayMetrics
    last_30_days: Last30DaysMetrics
    catalog: CatalogMetrics
    performance: PerformanceMetrics
    trends: TrendsMetrics

class SummaryMeta(BaseModel):
    """Summary response metadata"""
    merchant_id: str
    platform_shop_id: str
    generated_at: datetime

class SummaryResponse(BaseModel):
    """Analytics summary response"""
    data: SummaryData
    meta: SummaryMeta

# Shopper Analytics
class ShopperOverview(BaseModel):
    """Shopper overview metrics"""
    total_shoppers: int
    unique_shoppers: int
    returning_shoppers: int
    return_rate: float

class ShopperEngagement(BaseModel):
    """Shopper engagement metrics"""
    analyses_per_shopper: float
    match_rate: float
    avg_confidence: float

class DailyShopperBreakdown(BaseModel):
    """Daily shopper activity"""
    date: str
    shoppers: int
    matches: int

class ShopperAnalyticsData(BaseModel):
    """Shopper analytics response data"""
    overview: ShopperOverview
    engagement: ShopperEngagement
    daily_breakdown: List[DailyShopperBreakdown]

# Season Distribution
class SeasonMetrics(BaseModel):
    """Metrics for a season"""
    season: str
    shopper_count: int