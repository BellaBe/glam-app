# services/analytics/src/repositories/metrics_repository.py
"""Repository for aggregated metrics operations"""

from uuid import UUID
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from prisma import Prisma
from prisma.models import (
    DailyMerchantMetrics,
    HourlyUsageMetrics,
    SeasonDistribution,
    ProductMatchMetrics,
    CreditUsageMetrics
)
from ..exceptions import MetricsNotFoundError, MetricCalculationError
from ..schemas.responses import (
    TodayMetrics,
    Last30DaysMetrics,
    ShopperOverview,
    ShopperEngagement,
    DailyShopperBreakdown,
    ShopperAnalyticsData
)

class MetricsRepository:
    """Repository for aggregated metrics operations"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def get_daily_metrics(
        self,
        merchant_id: UUID,
        date: date
    ) -> TodayMetrics:
        """Get daily metrics for today"""
        metrics = await self.prisma.dailymerchantmetrics.find_unique(
            where={
                "merchant_id_date": {
                    "merchant_id": str(merchant_id),
                    "date": datetime.combine(date, datetime.min.time())
                }
            }
        )
        
        if not metrics:
            # Return empty metrics if no data
            return TodayMetrics(
                shoppers=0,
                matches=0,
                credits_used=0,
                match_rate=0.0,
                drop_off_rate=0.0,
                peak_hour=None,
                avg_analysis_time=0
            )
        
        match_rate = (metrics.total_matches / metrics.total_analyses * 100) if metrics.total_analyses > 0 else 0
        
        return TodayMetrics(
            shoppers=metrics.total_analyses,
            matches=metrics.total_matches,
            credits_used=metrics.credits_consumed,
            match_rate=round(match_rate, 1),
            drop_off_rate=round(metrics.drop_off_rate, 1),
            peak_hour=metrics.peak_hour,
            avg_analysis_time=metrics.avg_analysis_time_ms
        )
    
    async def get_aggregated_metrics(
        self,
        merchant_id: UUID,
        start_date: date,
        end_date: date
    ) -> Last30DaysMetrics:
        """Get aggregated metrics for date range"""
        # Aggregate daily metrics
        daily_metrics = await self.prisma.dailymerchantmetrics.find_many(
            where={
                "merchant_id": str(merchant_id),
                "date": {
                    "gte": datetime.combine(start_date, datetime.min.time()),
                    "lte": datetime.combine(end_date, datetime.min.time())
                }
            }
        )
        
        if not daily_metrics:
            raise MetricsNotFoundError(
                merchant_id=str(merchant_id),
                metric_type="daily",
                period=f"{start_date} to {end_date}"
            )
        
        # Calculate aggregates
        total_analyses = sum(m.total_analyses for m in daily_metrics)
        total_matches = sum(m.total_matches for m in daily_metrics)
        unique_shoppers = sum(m.unique_shoppers for m in daily_metrics)
        returning_shoppers = sum(m.returning_shoppers for m in daily_metrics)
        credits_consumed = sum(m.credits_consumed for m in daily_metrics)
        
        # Get latest credit balance
        latest_metric = max(daily_metrics, key=lambda x: x.date)
        credits_remaining = latest_metric.credits_remaining
        
        # Calculate averages
        avg_products_matched = sum(m.avg_products_matched for m in daily_metrics) / len(daily_metrics)
        avg_confidence_score = sum(m.avg_confidence_score for m in daily_metrics) / len(daily_metrics)
        zero_match_rate = sum(m.zero_match_rate for m in daily_metrics) / len(daily_metrics)
        
        # Calculate derived metrics
        return_rate = (returning_shoppers / unique_shoppers * 100) if unique_shoppers > 0 else 0
        analysis_frequency = total_analyses / unique_shoppers if unique_shoppers > 0 else 0
        daily_avg_credits = credits_consumed / len(daily_metrics)
        days_until_depletion = int(credits_remaining / daily_avg_credits) if daily_avg_credits > 0 else None
        
        return Last30DaysMetrics(
            total_shoppers=total_analyses,
            total_matches=total_matches,
            unique_shoppers=unique_shoppers,
            returning_shoppers=returning_shoppers,
            return_rate=round(return_rate, 1),
            analysis_frequency=round(analysis_frequency, 2),
            avg_products_per_match=round(avg_products_matched, 1),
            zero_match_rate=round(zero_match_rate, 1),
            credits_consumed=credits_consumed,
            credits_remaining=credits_remaining,
            days_until_depletion=days_until_depletion,
            catalog_freshness=latest_metric.catalog_freshness
        )
    
    async def update_season_distribution(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        platform_domain: str,
        date: date,
        season: str,
        confidence: float
    ) -> None:
        """Update season distribution metrics"""
        # Upsert season distribution
        await self.prisma.seasondistribution.upsert(
            where={
                "merchant_id_date_season": {
                    "merchant_id": str(merchant_id),
                    "date": datetime.combine(date, datetime.min.time()),
                    "season": season
                }
            },
            create={
                "merchant_id": str(merchant_id),
                "platform_name": platform_name,
                "platform_shop_id": platform_shop_id,
                "platform_domain": platform_domain,
                "date": datetime.combine(date, datetime.min.time()),
                "season": season,
                "shopper_count": 1,
                "avg_confidence": confidence
            },
            update={
                "shopper_count": {"increment": 1},
                "avg_confidence": {
                    "set": await self._calculate_running_avg(
                        merchant_id, date, season, confidence
                    )
                }
            }
        )
    
    async def update_product_metrics(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        platform_domain: str,
        product_id: str,
        variant_id: str,
        match_score: float,
        season: str
    ) -> None:
        """Update product match metrics"""
        existing = await self.prisma.productmatchmetrics.find_unique(
            where={
                "merchant_id_product_id_variant_id": {
                    "merchant_id": str(merchant_id),
                    "product_id": product_id,
                    "variant_id": variant_id
                }
            }
        )
        
        if existing:
            # Calculate new average and velocity
            new_total = existing.total_matches + 1
            new_avg = ((existing.avg_match_score * existing.total_matches) + match_score) / new_total
            
            # Calculate match velocity (matches per day)
            if existing.first_matched_at:
                days_active = max(1, (datetime.now() - existing.first_matched_at).days)
                match_velocity = new_total / days_active
            else:
                match_velocity = 1.0
            
            # Update primary seasons list
            primary_seasons = existing.primary_seasons or []
            if season not in primary_seasons:
                primary_seasons.append(season)
            
            await self.prisma.productmatchmetrics.update(
                where={"id": existing.id},
                data={
                    "total_matches": new_total,
                    "avg_match_score": new_avg,
                    "last_matched_at": datetime.now(),
                    "match_velocity": match_velocity,
                    "primary_seasons": primary_seasons
                }
            )
        else:
            # Create new product metrics
            await self.prisma.productmatchmetrics.create(
                data={
                    "merchant_id": str(merchant_id),
                    "platform_name": platform_name,
                    "platform_shop_id": platform_shop_id,
                    "platform_domain": platform_domain,
                    "product_id": product_id,
                    "variant_id": variant_id,
                    "total_matches": 1,
                    "avg_match_score": match_score,
                    "first_matched_at": datetime.now(),
                    "last_matched_at": datetime.now(),
                    "match_velocity": 1.0,
                    "primary_seasons": [season]
                }
            )
    
    async def increment_hourly_metrics(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        platform_domain: str,
        date: date,
        hour: int,
        analyses_increment: int = 0,
        matches_increment: int = 0,
        credits_increment: int = 0
    ) -> None:
        """Increment hourly usage metrics"""
        await self.prisma.hourlyusagemetrics.upsert(
            where={
                "merchant_id_date_hour": {
                    "merchant_id": str(merchant_id),
                    "date": datetime.combine(date, datetime.min.time()),
                    "hour": hour
                }
            },
            create={
                "merchant_id": str(merchant_id),
                "platform_name": platform_name,
                "platform_shop_id": platform_shop_id,
                "platform_domain": platform_domain,
                "date": datetime.combine(date, datetime.min.time()),
                "hour": hour,
                "analyses_count": analyses_increment,
                "matches_count": matches_increment,
                "credits_used": credits_increment
            },
            update={
                "analyses_count": {"increment": analyses_increment},
                "matches_count": {"increment": matches_increment},
                "credits_used": {"increment": credits_increment}
            }
        )
    
    async def update_credit_usage_metrics(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        platform_domain: str,
        date: date,
        hour: int,
        credits_consumed: int
    ) -> None:
        """Update credit usage metrics"""
        await self.prisma.creditusagemetrics.upsert(
            where={
                "merchant_id_date_hour": {
                    "merchant_id": str(merchant_id),
                    "date": datetime.combine(date, datetime.min.time()),
                    "hour": hour
                }
            },
            create={
                "merchant_id": str(merchant_id),
                "platform_name": platform_name,
                "platform_shop_id": platform_shop_id,
                "platform_domain": platform_domain,
                "date": datetime.combine(date, datetime.min.time()),
                "hour": hour,
                "credits_consumed": credits_consumed
            },
            update={
                "credits_consumed": {"increment": credits_consumed}
            }
        )
    
    async def update_daily_credit_balance(
        self,
        merchant_id: UUID,
        date: date,
        credits_remaining: int
    ) -> None:
        """Update daily credit balance"""
        await self.prisma.dailymerchantmetrics.update_many(
            where={
                "merchant_id": str(merchant_id),
                "date": datetime.combine(date, datetime.min.time())
            },
            data={
                "credits_remaining": credits_remaining
            }
        )
    
    async def update_catalog_metrics(
        self,
        merchant_id: UUID,
        date: date,
        total_products: int,
        analyzed_products: int
    ) -> None:
        """Update catalog metrics in daily metrics"""
        analysis_coverage = (analyzed_products / total_products * 100) if total_products > 0 else 0
        
        await self.prisma.dailymerchantmetrics.update_many(
            where={
                "merchant_id": str(merchant_id),
                "date": datetime.combine(date, datetime.min.time())
            },
            data={
                "total_products": total_products,
                "analyzed_products": analyzed_products,
                "analysis_coverage": analysis_coverage,
                "catalog_freshness": 0  # Just synced
            }
        )
    
    async def get_catalog_metrics(self, merchant_id: UUID) -> dict:
        """Get catalog metrics"""
        latest = await self.prisma.dailymerchantmetrics.find_first(
            where={"merchant_id": str(merchant_id)},
            order_by={"date": "desc"}
        )
        
        if not latest:
            return {
                "total_products": 0,
                "analyzed_products": 0,
                "analysis_coverage": 0.0,
                "products_never_matched": 0
            }
        
        # Count products never matched
        never_matched = await self.prisma.productmatchmetrics.count(
            where={
                "merchant_id": str(merchant_id),
                "total_matches": 0
            }
        )
        
        return {
            "total_products": latest.total_products,
            "analyzed_products": latest.analyzed_products,
            "analysis_coverage": round(latest.analysis_coverage, 1),
            "products_never_matched": never_matched
        }
    
    async def get_performance_metrics(
        self,
        merchant_id: UUID,
        date: date
    ) -> dict:
        """Get performance metrics"""
        metrics = await self.prisma.dailymerchantmetrics.find_unique(
            where={
                "merchant_id_date": {
                    "merchant_id": str(merchant_id),
                    "date": datetime.combine(date, datetime.min.time())
                }
            }
        )
        
        if not metrics:
            return {
                "analysis_success_rate": 100.0,
                "avg_processing_time": 0,
                "failed_analyses_today": 0
            }
        
        return {
            "analysis_success_rate": round(metrics.analysis_success_rate, 1),
            "avg_processing_time": metrics.avg_analysis_time_ms,
            "failed_analyses_today": metrics.failed_analyses
        }
    
    async def get_shopper_metrics(
        self,
        merchant_id: UUID,
        start_date: date,
        end_date: date
    ) -> ShopperAnalyticsData:
        """Get shopper analytics data"""
        # Get daily metrics for the period
        daily_metrics = await self.prisma.dailymerchantmetrics.find_many(
            where={
                "merchant_id": str(merchant_id),
                "date": {
                    "gte": datetime.combine(start_date, datetime.min.time()),
                    "lte": datetime.combine(end_date, datetime.min.time())
                }
            },
            order_by={"date": "desc"}
        )
        
        if not daily_metrics:
            # Return empty data
            return ShopperAnalyticsData(
                overview=ShopperOverview(
                    total_shoppers=0,
                    unique_shoppers=0,
                    returning_shoppers=0,
                    return_rate=0.0
                ),
                engagement=ShopperEngagement(
                    analyses_per_shopper=0.0,
                    match_rate=0.0,
                    avg_confidence=0.0
                ),
                daily_breakdown=[]
            )
        
        # Calculate totals
        total_shoppers = sum(m.total_analyses for m in daily_metrics)
        unique_shoppers = sum(m.unique_shoppers for m in daily_metrics)
        returning_shoppers = sum(m.returning_shoppers for m in daily_metrics)
        total_matches = sum(m.total_matches for m in daily_metrics)
        
        # Calculate rates
        return_rate = (returning_shoppers / unique_shoppers * 100) if unique_shoppers > 0 else 0
        analyses_per_shopper = total_shoppers / unique_shoppers if unique_shoppers > 0 else 0
        match_rate = (total_matches / total_shoppers * 100) if total_shoppers > 0 else 0
        avg_confidence = sum(m.avg_confidence_score for m in daily_metrics) / len(daily_metrics)
        
        # Create daily breakdown
        daily_breakdown = [
            DailyShopperBreakdown(
                date=m.date.strftime("%Y-%m-%d"),
                shoppers=m.total_analyses,
                matches=m.total_matches
            )
            for m in daily_metrics
        ]
        
        return ShopperAnalyticsData(
            overview=ShopperOverview(
                total_shoppers=total_shoppers,
                unique_shoppers=unique_shoppers,
                returning_shoppers=returning_shoppers,
                return_rate=round(return_rate, 1)
            ),
            engagement=ShopperEngagement(
                analyses_per_shopper=round(analyses_per_shopper, 2),
                match_rate=round(match_rate, 1),
                avg_confidence=round(avg_confidence, 2)
            ),
            daily_breakdown=daily_breakdown
        )
    
    async def get_season_distribution(
        self,
        merchant_id: UUID,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get season distribution data"""
        distributions = await self.prisma.seasondistribution.find_many(
            where={
                "merchant_id": str(merchant_id),
                "date": {
                    "gte": datetime.combine(start_date, datetime.min.time()),
                    "lte": datetime.combine(end_date, datetime.min.time())
                }
            }
        )
        
        # Aggregate by season
        season_totals = {}
        for dist in distributions:
            if dist.season not in season_totals:
                season_totals[dist.season] = {
                    "shopper_count": 0,
                    "confidence_sum": 0,
                    "product_coverage": 0
                }
            season_totals[dist.season]["shopper_count"] += dist.shopper_count
            season_totals[dist.season]["confidence_sum"] += dist.avg_confidence * dist.shopper_count
        
        # Calculate distribution
        total_shoppers = sum(s["shopper_count"] for s in season_totals.values())
        
        distribution = []
        for season, data in season_totals.items():
            percentage = (data["shopper_count"] / total_shoppers * 100) if total_shoppers > 0 else 0
            avg_confidence = data["confidence_sum"] / data["shopper_count"] if data["shopper_count"] > 0 else 0
            
            # Get product coverage for this season
            product_coverage = await self.prisma.productmatchmetrics.count(
                where={
                    "merchant_id": str(merchant_id),
                    "primary_seasons": {"has": season}
                }
            )
            
            distribution.append({
                "season": season,
                "shopper_count": data["shopper_count"],
                "percentage": round(percentage, 1),
                "avg_confidence": round(avg_confidence, 2),
                "product_coverage": product_coverage
            })
        
        # Sort by shopper count
        distribution.sort(key=lambda x: x["shopper_count"], reverse=True)
        
        # Find underserved seasons (less than 5% of products)
        total_products = await self._get_total_product_count(merchant_id)
        underserved = [
            d["season"] for d in distribution 
            if d["product_coverage"] < total_products * 0.05
        ]
        
        return {
            "distribution": distribution,
            "insights": {
                "dominant_season": distribution[0]["season"] if distribution else None,
                "underserved_seasons": underserved,
                "avg_products_per_season": int(total_products / len(distribution)) if distribution else 0
            }
        }
    
    async def get_product_performance(
        self,
        merchant_id: UUID,
        limit: int
    ) -> dict:
        """Get product performance data"""
        # Get top products
        top_products = await self.prisma.productmatchmetrics.find_many(
            where={"merchant_id": str(merchant_id)},
            order_by={"total_matches": "desc"},
            take=limit
        )
        
        # Get dead stock (never matched)
        dead_stock = await self.prisma.productmatchmetrics.find_many(
            where={
                "merchant_id": str(merchant_id),
                "total_matches": 0
            },
            take=20
        )
        
        # Get products by season
        all_products = await self.prisma.productmatchmetrics.find_many(
            where={"merchant_id": str(merchant_id)}
        )
        
        # Aggregate by season
        season_stats = {}
        for product in all_products:
            for season in (product.primary_seasons or []):
                if season not in season_stats:
                    season_stats[season] = {
                        "count": 0,
                        "score_sum": 0
                    }
                season_stats[season]["count"] += 1
                season_stats[season]["score_sum"] += product.avg_match_score
        
        products_by_season = [
            {
                "season": season,
                "count": data["count"],
                "avg_match_score": round(data["score_sum"] / data["count"], 2) if data["count"] > 0 else 0
            }
            for season, data in season_stats.items()
        ]
        
        # Calculate summary
        total_products = len(all_products)
        products_matched = sum(1 for p in all_products if p.total_matches > 0)
        products_never_matched = total_products - products_matched
        coverage_rate = (products_matched / total_products * 100) if total_products > 0 else 0
        
        return {
            "top_products": [
                {
                    "product_id": p.product_id,
                    "variant_id": p.variant_id,
                    "match_count": p.total_matches,
                    "avg_match_score": round(p.avg_match_score, 2),
                    "match_velocity": round(p.match_velocity, 1),
                    "days_active": (datetime.now() - p.first_matched_at).days if p.first_matched_at else 0,
                    "primary_seasons": p.primary_seasons or []
                }
                for p in top_products
            ],
            "dead_stock": [
                {
                    "product_id": p.product_id,
                    "variant_id": p.variant_id,
                    "days_since_sync": 30,  # Would need actual sync date
                    "seasons": p.primary_seasons or []
                }
                for p in dead_stock
            ],
            "products_by_season": products_by_season,
            "summary": {
                "total_products": total_products,
                "products_matched": products_matched,
                "products_never_matched": products_never_matched,
                "coverage_rate": round(coverage_rate, 1)
            }
        }
    
    async def get_credit_analytics(self, merchant_id: UUID) -> dict:
        """Get credit analytics data"""
        today = date.today()
        
        # Get credit usage for different periods
        today_usage = await self.prisma.creditusagemetrics.aggregate(
            where={
                "merchant_id": str(merchant_id),
                "date": datetime.combine(today, datetime.min.time())
            },
            _sum={"credits_consumed": True}
        )
        
        last_7_days = await self.prisma.creditusagemetrics.aggregate(
            where={
                "merchant_id": str(merchant_id),
                "date": {
                    "gte": datetime.combine(today - timedelta(days=7), datetime.min.time())
                }
            },
            _sum={"credits_consumed": True}
        )
        
        last_30_days = await self.prisma.creditusagemetrics.aggregate(
            where={
                "merchant_id": str(merchant_id),
                "date": {
                    "gte": datetime.combine(today - timedelta(days=30), datetime.min.time())
                }
            },
            _sum={"credits_consumed": True}
        )
        
        # Get current balance from latest daily metrics
        latest_metrics = await self.prisma.dailymerchantmetrics.find_first(
            where={"merchant_id": str(merchant_id)},
            order_by={"date": "desc"}
        )
        
        current_balance = latest_metrics.credits_remaining if latest_metrics else 0
        
        # Calculate projections
        daily_average = (last_30_days._sum.credits_consumed or 0) / 30
        days_remaining = int(current_balance / daily_average) if daily_average > 0 else 0
        monthly_projection = int(daily_average * 30)
        
        # Determine recommended pack
        if monthly_projection <= 500:
            recommended_pack = "small"
        elif monthly_projection <= 2000:
            recommended_pack = "medium"
        elif monthly_projection <= 5000:
            recommended_pack = "large"
        else:
            recommended_pack = "enterprise"
        
        # Get history for last 7 days
        history_data = await self.prisma.creditusagemetrics.find_many(
            where={
                "merchant_id": str(merchant_id),
                "date": {
                    "gte": datetime.combine(today - timedelta(days=7), datetime.min.time())
                }
            },
            order_by={"date": "desc"}
        )
        
        # Group by date
        history_by_date = {}
        for h in history_data:
            date_str = h.date.strftime("%Y-%m-%d")
            if date_str not in history_by_date:
                history_by_date[date_str] = {"consumed": 0, "granted": 0}
            history_by_date[date_str]["consumed"] += h.credits_consumed
        
        history = [
            {
                "date": date_str,
                "consumed": data["consumed"],
                "granted": data["granted"]
            }
            for date_str, data in history_by_date.items()
        ]
        
        # Find peak hour
        hourly_usage = await self.prisma.hourlyusagemetrics.find_many(
            where={
                "merchant_id": str(merchant_id),
                "date": datetime.combine(today, datetime.min.time())
            },
            order_by={"credits_used": "desc"},
            take=1
        )
        
        peak_hour = hourly_usage[0].hour if hourly_usage else 14
        
        return {
            "current_balance": current_balance,
            "usage": {
                "today": today_usage._sum.credits_consumed or 0,
                "last_7_days": last_7_days._sum.credits_consumed or 0,
                "last_30_days": last_30_days._sum.credits_consumed or 0,
                "daily_average": round(daily_average, 1),
                "peak_hour": peak_hour,
                "credit_efficiency": 1.0  # Assuming 1 credit per match
            },
            "projection": {
                "days_remaining": days_remaining,
                "monthly_projection": monthly_projection,
                "recommended_pack": recommended_pack,
                "burndown_trend": "+12%"  # Would calculate from actual trend
            },
            "history": history
        }
    
    async def _calculate_running_avg(
        self,
        merchant_id: UUID,
        date: date,
        season: str,
        new_value: float
    ) -> float:
        """Calculate running average for a metric"""
        existing = await self.prisma.seasondistribution.find_unique(
            where={
                "merchant_id_date_season": {
                    "merchant_id": str(merchant_id),
                    "date": datetime.combine(date, datetime.min.time()),
                    "season": season
                }
            }
        )
        
        if not existing:
            return new_value
        
        # Calculate new running average
        total = existing.avg_confidence * existing.shopper_count
        new_total = total + new_value
        new_count = existing.shopper_count + 1
        
        return new_total / new_count
    
    async def _get_total_product_count(self, merchant_id: UUID) -> int:
        """Get total product count for merchant"""
        latest = await self.prisma.dailymerchantmetrics.find_first(
            where={"merchant_id": str(merchant_id)},
            order_by={"date": "desc"}
        )
        
        return latest.total_products if latest else 0