# services/analytics/src/services/analytics_service.py
from datetime import datetime, timedelta
from uuid import UUID

from shared.utils.logger import ServiceLogger

from ..exceptions import InsufficientDataError, InvalidPeriodError, MetricCalculationError, MetricsNotFoundError
from ..repositories.analytics_repository import AnalyticsRepository
from ..repositories.metrics_repository import MetricsRepository
from ..schemas.events import RecommendationMatchCompletedPayload, SelfieAnalysisCompletedPayload
from ..schemas.responses import (
    CatalogMetrics,
    CreditAnalyticsData,
    PerformanceMetrics,
    ProductPerformanceData,
    SeasonDistributionData,
    ShopperAnalyticsData,
    SummaryData,
    TodayMetrics,
    TrendsMetrics,
)


class AnalyticsService:
    """Core analytics business logic"""

    def __init__(self, analytics_repo: AnalyticsRepository, metrics_repo: MetricsRepository, logger: ServiceLogger):
        self.analytics_repo = analytics_repo
        self.metrics_repo = metrics_repo
        self.logger = logger

    async def record_analytics_event(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        domain: str,
        event_type: str,
        event_data: dict,
        shopper_id: str | None = None,
        anonymous_id: str | None = None,
        analysis_id: str | None = None,
        match_id: str | None = None,
    ) -> None:
        """Record raw analytics event"""
        try:
            await self.analytics_repo.create_event(
                merchant_id=merchant_id,
                platform_name=platform_name,
                platform_shop_id=platform_shop_id,
                domain=domain,
                event_type=event_type,
                event_data=event_data,
                shopper_id=shopper_id,
                anonymous_id=anonymous_id,
                analysis_id=analysis_id,
                match_id=match_id,
            )
        except Exception as e:
            # Log but don't fail - raw events are best effort
            self.logger.exception(
                f"Failed to record analytics event: {e}",
                extra={"merchant_id": str(merchant_id), "event_type": event_type},
            )

    async def record_shopper_analysis(self, payload: SelfieAnalysisCompletedPayload) -> None:
        """Record shopper analysis metrics"""
        try:
            await self.analytics_repo.create_shopper_analysis(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                shopper_id=payload.shopper_id,
                anonymous_id=payload.anonymous_id,
                analysis_id=payload.analysis_id,
                primary_season=payload.primary_season,
                secondary_season=payload.secondary_season,
                tertiary_season=payload.tertiary_season,
                confidence=payload.confidence,
                processing_time_ms=payload.processing_time_ms,
            )

            # Update season distribution
            await self.metrics_repo.update_season_distribution(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                date=payload.analyzed_at.date(),
                season=payload.primary_season,
                confidence=payload.confidence,
            )
        except Exception as e:
            self.logger.exception(
                f"Failed to record shopper analysis: {e}",
                extra={"analysis_id": payload.analysis_id, "merchant_id": str(payload.merchant_id)},
            )
            raise

    async def record_match_metrics(self, payload: RecommendationMatchCompletedPayload) -> None:
        """Record match metrics"""
        try:
            await self.analytics_repo.create_match_metrics(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                match_id=payload.match_id,
                shopper_id=payload.shopper_id,
                anonymous_id=payload.anonymous_id,
                analysis_id=payload.analysis_id,
                total_matches=payload.total_matches,
                products_matched=[p["product_id"] for p in payload.products_matched],
                avg_match_score=payload.avg_match_score,
                top_match_score=payload.top_match_score,
                primary_season=payload.primary_season,
                credits_consumed=payload.credits_consumed,
            )
        except Exception as e:
            self.logger.exception(
                f"Failed to record match metrics: {e}",
                extra={"match_id": payload.match_id, "merchant_id": str(payload.merchant_id)},
            )
            raise

    async def update_product_metrics(self, payload: RecommendationMatchCompletedPayload) -> None:
        """Update product performance metrics"""
        for product in payload.products_matched:
            try:
                await self.metrics_repo.update_product_metrics(
                    merchant_id=payload.merchant_id,
                    platform_name=payload.platform_name,
                    platform_shop_id=payload.platform_shop_id,
                    domain=payload.domain,
                    product_id=product["product_id"],
                    variant_id=product["variant_id"],
                    match_score=product["score"],
                    season=product.get("season", payload.primary_season),
                )
            except Exception as e:
                # Log but continue with other products
                self.logger.exception(
                    f"Failed to update product metrics: {e}",
                    extra={"product_id": product["product_id"], "merchant_id": str(payload.merchant_id)},
                )

    async def update_hourly_metrics(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        domain: str,
        timestamp: datetime,
        analyses_increment: int = 0,
        matches_increment: int = 0,
        credits_increment: int = 0,
    ) -> None:
        """Update hourly usage metrics"""
        try:
            await self.metrics_repo.increment_hourly_metrics(
                merchant_id=merchant_id,
                platform_name=platform_name,
                platform_shop_id=platform_shop_id,
                domain=domain,
                date=timestamp.date(),
                hour=timestamp.hour,
                analyses_increment=analyses_increment,
                matches_increment=matches_increment,
                credits_increment=credits_increment,
            )
        except Exception as e:
            self.logger.exception(
                f"Failed to update hourly metrics: {e}",
                extra={"merchant_id": str(merchant_id), "timestamp": timestamp.isoformat()},
            )

    async def update_credit_usage(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        domain: str,
        timestamp: datetime,
        credits_consumed: int,
        remaining_balance: int,
    ) -> None:
        """Update credit usage metrics"""
        try:
            await self.metrics_repo.update_credit_usage_metrics(
                merchant_id=merchant_id,
                platform_name=platform_name,
                platform_shop_id=platform_shop_id,
                domain=domain,
                date=timestamp.date(),
                hour=timestamp.hour,
                credits_consumed=credits_consumed,
            )

            # Store current balance for daily metrics
            await self.metrics_repo.update_daily_credit_balance(
                merchant_id=merchant_id, date=timestamp.date(), credits_remaining=remaining_balance
            )
        except Exception as e:
            self.logger.exception(
                f"Failed to update credit usage: {e}",
                extra={"merchant_id": str(merchant_id), "credits_consumed": credits_consumed},
            )

    async def update_catalog_metrics(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        domain: str,
        total_products: int,
        analyzed_products: int,
        synced_at: datetime,
    ) -> None:
        """Update catalog metrics"""
        try:
            await self.metrics_repo.update_catalog_metrics(
                merchant_id=merchant_id,
                date=synced_at.date(),
                total_products=total_products,
                analyzed_products=analyzed_products,
            )
        except Exception as e:
            self.logger.exception(
                f"Failed to update catalog metrics: {e}",
                extra={"merchant_id": str(merchant_id), "total_products": total_products},
            )

    async def get_summary_analytics(self, merchant_id: UUID, platform_shop_id: str, correlation_id: str) -> SummaryData:
        """Get summary analytics for merchant"""
        today = datetime.now().date()
        last_30_days_start = today - timedelta(days=30)

        try:
            # Get today's metrics
            today_metrics = await self.metrics_repo.get_daily_metrics(merchant_id=merchant_id, date=today)
        except Exception:
            # If no metrics for today, return empty metrics
            today_metrics = TodayMetrics(
                shoppers=0,
                matches=0,
                credits_used=0,
                match_rate=0.0,
                drop_off_rate=0.0,
                peak_hour=None,
                avg_analysis_time=0,
            )

        try:
            # Get last 30 days aggregated
            last_30_metrics = await self.metrics_repo.get_aggregated_metrics(
                merchant_id=merchant_id, start_date=last_30_days_start, end_date=today
            )
        except MetricsNotFoundError:
            # Return insufficient data error
            raise InsufficientDataError(metric_type="summary", minimum_required=1, actual_count=0)

        # Get catalog metrics
        catalog_metrics = await self.metrics_repo.get_catalog_metrics(merchant_id=merchant_id)

        # Get performance metrics
        performance_metrics = await self.metrics_repo.get_performance_metrics(merchant_id=merchant_id, date=today)

        # Calculate trends
        try:
            trends = await self._calculate_trends(merchant_id, today)
        except Exception:
            # Default trends if calculation fails
            trends = TrendsMetrics(shopper_growth="N/A", match_rate=0.0, daily_avg_credits=0.0)

        self.logger.info(
            "Generated summary analytics",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": str(merchant_id),
                "platform_shop_id": platform_shop_id,
            },
        )

        return SummaryData(
            today=today_metrics,
            last_30_days=last_30_metrics,
            catalog=CatalogMetrics(**catalog_metrics),
            performance=PerformanceMetrics(**performance_metrics),
            trends=trends,
        )

    async def get_shopper_analytics(
        self, merchant_id: UUID, period_days: int, correlation_id: str
    ) -> ShopperAnalyticsData:
        """Get shopper analytics"""
        # Validate period
        if period_days not in [7, 30]:
            raise InvalidPeriodError(period=f"{period_days}d", valid_periods=["7d", "30d"])

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days)

        try:
            shopper_data = await self.metrics_repo.get_shopper_metrics(
                merchant_id=merchant_id, start_date=start_date, end_date=end_date
            )
        except Exception:
            raise MetricsNotFoundError(
                merchant_id=str(merchant_id), metric_type="shopper", period=f"{period_days} days"
            )

        # Check for insufficient data
        if shopper_data.overview.total_shoppers < 10:
            self.logger.warning(
                "Insufficient shopper data",
                extra={"merchant_id": str(merchant_id), "total_shoppers": shopper_data.overview.total_shoppers},
            )

        self.logger.info(
            "Generated shopper analytics",
            extra={"correlation_id": correlation_id, "merchant_id": str(merchant_id), "period_days": period_days},
        )

        return shopper_data

    async def get_season_distribution(
        self, merchant_id: UUID, period_days: int, correlation_id: str
    ) -> SeasonDistributionData:
        """Get season distribution analytics"""
        # Validate period
        if period_days not in [7, 30]:
            raise InvalidPeriodError(period=f"{period_days}d", valid_periods=["7d", "30d"])

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days)

        try:
            season_data = await self.metrics_repo.get_season_distribution(
                merchant_id=merchant_id, start_date=start_date, end_date=end_date
            )
        except Exception:
            raise MetricsNotFoundError(merchant_id=str(merchant_id), metric_type="season", period=f"{period_days} days")

        if not season_data.get("distribution"):
            raise InsufficientDataError(metric_type="season distribution", minimum_required=1, actual_count=0)

        self.logger.info(
            "Generated season distribution",
            extra={"correlation_id": correlation_id, "merchant_id": str(merchant_id), "period_days": period_days},
        )

        return SeasonDistributionData(**season_data)

    async def get_product_performance(
        self, merchant_id: UUID, limit: int, correlation_id: str
    ) -> ProductPerformanceData:
        """Get product performance analytics"""
        if limit < 1 or limit > 100:
            raise InvalidPeriodError(period=f"limit={limit}", valid_periods=["1-100"])

        try:
            product_data = await self.metrics_repo.get_product_performance(merchant_id=merchant_id, limit=limit)
        except Exception:
            raise MetricsNotFoundError(merchant_id=str(merchant_id), metric_type="product performance")

        if product_data["summary"]["total_products"] == 0:
            raise InsufficientDataError(metric_type="product performance", minimum_required=1, actual_count=0)

        self.logger.info(
            "Generated product performance",
            extra={"correlation_id": correlation_id, "merchant_id": str(merchant_id), "limit": limit},
        )

        return ProductPerformanceData(**product_data)

    async def get_credit_analytics(self, merchant_id: UUID, correlation_id: str) -> CreditAnalyticsData:
        """Get credit usage analytics"""
        try:
            credit_data = await self.metrics_repo.get_credit_analytics(merchant_id=merchant_id)
        except Exception:
            raise MetricsNotFoundError(merchant_id=str(merchant_id), metric_type="credit usage")

        self.logger.info(
            "Generated credit analytics", extra={"correlation_id": correlation_id, "merchant_id": str(merchant_id)}
        )

        return CreditAnalyticsData(**credit_data)

    async def _calculate_trends(self, merchant_id: UUID, reference_date: datetime.date) -> TrendsMetrics:
        """Calculate trend metrics"""
        try:
            # Compare this week vs last week
            this_week_start = reference_date - timedelta(days=7)
            last_week_start = reference_date - timedelta(days=14)

            this_week_metrics = await self.metrics_repo.get_aggregated_metrics(
                merchant_id=merchant_id, start_date=this_week_start, end_date=reference_date
            )

            last_week_metrics = await self.metrics_repo.get_aggregated_metrics(
                merchant_id=merchant_id, start_date=last_week_start, end_date=this_week_start
            )

            # Calculate growth percentage
            if last_week_metrics.unique_shoppers > 0:
                growth = (
                    (this_week_metrics.unique_shoppers - last_week_metrics.unique_shoppers)
                    / last_week_metrics.unique_shoppers
                    * 100
                )
                growth_str = f"{'+' if growth > 0 else ''}{growth:.1f}%"
            else:
                growth_str = "N/A"

            # Calculate match rate
            match_rate = (
                (this_week_metrics.total_matches / this_week_metrics.total_shoppers * 100)
                if this_week_metrics.total_shoppers > 0
                else 0.0
            )

            # Calculate daily average credits
            daily_avg_credits = this_week_metrics.credits_consumed / 7

            return TrendsMetrics(
                shopper_growth=growth_str,
                match_rate=round(match_rate, 1),
                daily_avg_credits=round(daily_avg_credits, 1),
            )

        except Exception as e:
            raise MetricCalculationError(
                metric_name="trends",
                reason=str(e),
                data={"merchant_id": str(merchant_id), "reference_date": str(reference_date)},
            )
