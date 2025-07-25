from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from shared.utils.logger import ServiceLogger
from ..repositories.analytics_repository import (
    AnalyticsRepository, OrderAnalyticsRepository, LifecycleTrialAnalyticsRepository,
    UsagePatternRepository, PredictionModelRepository, EngagementMetricRepository,
    ShopifyAnalyticsRepository
)
from ..mappers.analytics_mapper import (
    UsageAnalyticsMapper, OrderAnalyticsMapper, LifecycleTrialAnalyticsMapper,
    UsagePatternMapper, PredictionModelMapper, EngagementMetricMapper,
    ShopifyAnalyticsMapper
)
from ..schemas.analytics import (
    UsageAnalyticsIn, UsageAnalyticsOut, OrderAnalyticsOut,
    LifecycleTrialAnalyticsOut, UsagePatternOut, PredictionModelOut,
    EngagementMetricOut, ShopifyAnalyticsOut, AnalyticsInsightOut,
    UsageTrendOut, ChurnRiskOut
)
from ..events.publishers import AnalyticsEventPublisher
from ..events.types import AnalyticsEvents
from ..exceptions import AnalyticsError, AnalyticsNotFoundError
from ..models.enums import PatternType, PredictionType, EngagementPeriod
from .pattern_detection_service import PatternDetectionService
from .prediction_service import PredictionService

class AnalyticsService:
    """Core analytics service for processing and analyzing data"""
    
    def __init__(
        self,
        usage_repo: AnalyticsRepository,
        order_repo: OrderAnalyticsRepository,
        trial_repo: LifecycleTrialAnalyticsRepository,
        pattern_repo: UsagePatternRepository,
        prediction_repo: PredictionModelRepository,
        engagement_repo: EngagementMetricRepository,
        shopify_repo: ShopifyAnalyticsRepository,
        usage_mapper: UsageAnalyticsMapper,
        order_mapper: OrderAnalyticsMapper,
        trial_mapper: LifecycleTrialAnalyticsMapper,
        pattern_mapper: UsagePatternMapper,
        prediction_mapper: PredictionModelMapper,
        engagement_mapper: EngagementMetricMapper,
        shopify_mapper: ShopifyAnalyticsMapper,
        publisher: AnalyticsEventPublisher,
        pattern_service: PatternDetectionService,
        prediction_service: PredictionService,
        logger: ServiceLogger,
        config
    ):
        self.usage_repo = usage_repo
        self.order_repo = order_repo
        self.trial_repo = trial_repo
        self.pattern_repo = pattern_repo
        self.prediction_repo = prediction_repo
        self.engagement_repo = engagement_repo
        self.shopify_repo = shopify_repo
        
        self.usage_mapper = usage_mapper
        self.order_mapper = order_mapper
        self.trial_mapper = trial_mapper
        self.pattern_mapper = pattern_mapper
        self.prediction_mapper = prediction_mapper
        self.engagement_mapper = engagement_mapper
        self.shopify_mapper = shopify_mapper
        
        self.publisher = publisher
        self.pattern_service = pattern_service
        self.prediction_service = prediction_service
        self.logger = logger
        self.config = config
    
    # ========== Event Processing ==========
    
    async def process_credit_consumption(self, payload: Dict[str, Any], correlation_id: str):
        """Process credit consumption event"""
        merchant_id = UUID(payload["merchant_id"])
        credits_consumed = Decimal(str(payload["credits_consumed"]))
        feature_name = payload.get("feature_name", "unknown")
        
        # Update daily usage analytics
        today = date.today()
        usage_analytics = await self.usage_repo.find_by_merchant_and_date(merchant_id, today)
        
        if not usage_analytics:
            # Create new daily record
            usage_data = UsageAnalyticsIn(
                date=today,
                feature_usage={feature_name: {"requests": 1, "credits": float(credits_consumed)}},
                total_credits_consumed=credits_consumed,
                api_calls=1
            )
            model = self.usage_mapper.to_model(usage_data, merchant_id=merchant_id)
            await self.usage_repo.save(model)
        else:
            # Update existing record
            feature_usage = usage_analytics.feature_usage.copy()
            if feature_name in feature_usage:
                feature_usage[feature_name]["requests"] += 1
                feature_usage[feature_name]["credits"] += float(credits_consumed)
            else:
                feature_usage[feature_name] = {"requests": 1, "credits": float(credits_consumed)}
            
            usage_analytics.feature_usage = feature_usage
            usage_analytics.total_credits_consumed += credits_consumed
            usage_analytics.api_calls += 1
            await self.usage_repo.save(usage_analytics)
        
        # Check for patterns and anomalies
        await self._check_usage_patterns(merchant_id, correlation_id)
        
        self.logger.info(
            "Processed credit consumption",
            extra={
                "merchant_id": str(merchant_id),
                "credits_consumed": str(credits_consumed),
                "feature_name": feature_name,
                "correlation_id": correlation_id
            }
        )
    
    async def process_ai_usage(self, payload: Dict[str, Any], subject: str, correlation_id: str):
        """Process AI feature usage event"""
        merchant_id = UUID(payload["merchant_id"])
        feature_name = self._extract_feature_from_event(subject)
        
        # Update feature-specific metrics
        today = date.today()
        usage_analytics = await self.usage_repo.find_by_merchant_and_date(merchant_id, today)
        
        if usage_analytics:
            feature_usage = usage_analytics.feature_usage.copy()
            if feature_name not in feature_usage:
                feature_usage[feature_name] = {"requests": 0, "success": 0, "failures": 0}
            
            feature_usage[feature_name]["requests"] += 1
            
            # Track success/failure based on event type
            if "failed" in subject:
                feature_usage[feature_name]["failures"] += 1
            else:
                feature_usage[feature_name]["success"] += 1
            
            # Add performance metrics if available
            if "processing_time_ms" in payload:
                if "avg_processing_time" not in feature_usage[feature_name]:
                    feature_usage[feature_name]["avg_processing_time"] = []
                feature_usage[feature_name]["avg_processing_time"].append(
                    payload["processing_time_ms"]
                )
            
            usage_analytics.feature_usage = feature_usage
            await self.usage_repo.save(usage_analytics)
    
    async def process_merchant_lifecycle(self, payload: Dict[str, Any], subject: str, correlation_id: str):
        """Process merchant lifecycle event"""
        merchant_id = UUID(payload["merchant_id"])
        
        # Handle trial-related events
        if "trial" in subject.lower():
            await self._process_trial_event(merchant_id, payload, subject, correlation_id)
        
        # Handle conversion events
        if "converted" in subject.lower() or "subscription" in subject.lower():
            await self._process_conversion_event(merchant_id, payload, correlation_id)
    
    async def process_shopify_event(self, payload: Dict[str, Any], subject: str, correlation_id: str):
        """Process Shopify integration event"""
        merchant_id = UUID(payload["merchant_id"])
        shop_id = payload.get("shop_id", "")
        
        # Update Shopify analytics
        today = date.today()
        shopify_analytics = await self.shopify_repo.find_by_merchant_and_date(merchant_id, today)
        
        if not shopify_analytics:
            from ..models.analytics import ShopifyAnalytics
            shopify_analytics = ShopifyAnalytics(
                merchant_id=merchant_id,
                merchant_domain=payload.get("merchant_domain", ""),
                shop_id=shop_id,
                date=today
            )
        
        # Update based on event type
        if "webhook" in subject:
            if "failed" in subject:
                shopify_analytics.webhook_events_failed += 1
            else:
                shopify_analytics.webhook_events_processed += 1
        elif "api" in subject:
            if "failed" in subject:
                shopify_analytics.api_calls_failed += 1
            else:
                shopify_analytics.api_calls_made += 1
        elif "rate_limit" in subject:
            shopify_analytics.api_rate_limit_hits += 1
        
        await self.shopify_repo.save(shopify_analytics)
    
    async def process_auth_event(self, payload: Dict[str, Any], subject: str, correlation_id: str):
        """Process authentication event for session tracking"""
        merchant_id = UUID(payload["merchant_id"])
        
        # Update engagement metrics based on auth events
        if "session_created" in subject:
            await self._update_session_metrics(merchant_id, payload)
        elif "session_ended" in subject:
            await self._update_session_duration(merchant_id, payload)
    
    # ========== Analytics Queries ==========
    
    async def get_usage_analytics(
        self, 
        merchant_id: UUID, 
        start_date: date, 
        end_date: date
    ) -> List[UsageAnalyticsOut]:
        """Get usage analytics for date range"""
        analytics = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        return self.usage_mapper.list_to_out(analytics)
    
    async def get_usage_trends(
        self, 
        merchant_id: UUID, 
        timeframe: str = "30d",
        compare_period: str = "previous"
    ) -> UsageTrendOut:
        """Get usage trend analysis"""
        days = self._parse_timeframe(timeframe)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get current period data
        current_data = await self.usage_repo.get_daily_aggregates(merchant_id, days)
        
        # Get comparison period data
        comparison_start = start_date - timedelta(days=days)
        comparison_end = start_date
        
        previous_analytics = await self.usage_repo.find_usage_trends(
            merchant_id, comparison_start, comparison_end
        )
        
        previous_credits = sum(a.total_credits_consumed for a in previous_analytics)
        current_credits = current_data["total_credits"]
        
        if previous_credits > 0:
            percentage_change = ((current_credits - previous_credits) / previous_credits) * 100
        else:
            percentage_change = 100.0 if current_credits > 0 else 0.0
        
        trend_direction = "up" if percentage_change > 5 else "down" if percentage_change < -5 else "stable"
        
        return UsageTrendOut(
            period=timeframe,
            trend_direction=trend_direction,
            percentage_change=Decimal(str(percentage_change)),
            current_value=current_credits,
            previous_value=previous_credits,
            data_points=self._format_trend_data(await self.usage_repo.find_usage_trends(
                merchant_id, start_date, end_date
            ))
        )
    
    async def get_order_analytics(self, merchant_id: UUID, target_date: date) -> Optional[OrderAnalyticsOut]:
        """Get order analytics for specific date"""
        order_analytics = await self.order_repo.find_by_merchant_and_date(merchant_id, target_date)
        return self.order_mapper.to_out(order_analytics) if order_analytics else None
    
    async def get_trial_analytics(self, merchant_id: UUID) -> Optional[LifecycleTrialAnalyticsOut]:
        """Get trial analytics for merchant"""
        trial_analytics = await self.trial_repo.find_by_merchant(merchant_id)
        return self.trial_mapper.to_out(trial_analytics) if trial_analytics else None
    
    async def get_usage_patterns(
        self, 
        merchant_id: UUID, 
        pattern_types: Optional[List[PatternType]] = None,
        confidence_threshold: float = 0.7
    ) -> List[UsagePatternOut]:
        """Get usage patterns for merchant"""
        if pattern_types:
            patterns = []
            for pattern_type in pattern_types:
                type_patterns = await self.pattern_repo.find_by_merchant_and_type(
                    merchant_id, pattern_type
                )
                patterns.extend(type_patterns)
        else:
            patterns = await self.pattern_repo.find_valid_patterns(merchant_id)
        
        # Filter by confidence threshold
        filtered_patterns = [p for p in patterns if p.confidence_score >= confidence_threshold]
        
        return self.pattern_mapper.list_to_out(filtered_patterns)
    
    async def get_predictions(
        self, 
        merchant_id: UUID, 
        prediction_types: Optional[List[PredictionType]] = None
    ) -> List[PredictionModelOut]:
        """Get predictions for merchant"""
        if not prediction_types:
            prediction_types = list(PredictionType)
        
        predictions = []
        for pred_type in prediction_types:
            type_predictions = await self.prediction_repo.find_by_merchant_and_type(
                merchant_id, pred_type, limit=5
            )
            predictions.extend(type_predictions)
        
        return self.prediction_mapper.list_to_out(predictions)
    
    async def get_churn_risk(self, merchant_id: UUID) -> Optional[ChurnRiskOut]:
        """Get churn risk assessment for merchant"""
        latest_prediction = await self.prediction_repo.find_latest_prediction(
            merchant_id, PredictionType.CHURN_RISK
        )
        
        if not latest_prediction:
            # Generate new prediction if none exists
            return await self.prediction_service.predict_churn_risk(merchant_id)
        
        return ChurnRiskOut(
            merchant_id=merchant_id,
            risk_score=latest_prediction.prediction_value,
            risk_level=self._calculate_risk_level(latest_prediction.prediction_value),
            factors=latest_prediction.factors.get("risk_factors", []) if latest_prediction.factors else [],
            recommended_actions=latest_prediction.factors.get("recommendations", []) if latest_prediction.factors else [],
            predicted_churn_date=latest_prediction.prediction_date,
            confidence=latest_prediction.confidence_interval.get("confidence", 0.5) if latest_prediction.confidence_interval else 0.5
        )
    
    async def get_engagement_metrics(
        self, 
        merchant_id: UUID, 
        period: EngagementPeriod = EngagementPeriod.MONTHLY,
        include_benchmarks: bool = False
    ) -> List[EngagementMetricOut]:
        """Get engagement metrics for merchant"""
        metrics = await self.engagement_repo.find_by_merchant_and_period(merchant_id, period)
        result = self.engagement_mapper.list_to_out(metrics)
        
        if include_benchmarks and result:
            # Add benchmark data (this would come from platform aggregates)
            for metric in result:
                # This is a simplified benchmark - in practice, you'd calculate from platform data
                metric.__dict__["benchmarks"] = {
                    "industry_avg_engagement": 0.65,
                    "platform_avg_retention": 0.75,
                    "top_quartile_threshold": 0.85
                }
        
        return result
    
    # ========== Analytics Insights ==========
    
    async def generate_insights(self, merchant_id: UUID) -> List[AnalyticsInsightOut]:
        """Generate actionable insights for merchant"""
        insights = []
        
        # Usage trend insights
        trend = await self.get_usage_trends(merchant_id)
        if trend.percentage_change > 20:
            insights.append(AnalyticsInsightOut(
                insight_type="usage_growth",
                title="Strong Usage Growth Detected",
                description=f"Your usage has increased by {trend.percentage_change:.1f}% compared to the previous period.",
                metrics={"growth_rate": float(trend.percentage_change)},
                recommendations=[
                    "Consider upgrading your plan to accommodate increased usage",
                    "Explore additional features that complement your high-usage patterns"
                ],
                confidence=Decimal("0.95"),
                created_at=datetime.utcnow()
            ))
        
        # Pattern-based insights
        patterns = await self.get_usage_patterns(merchant_id)
        for pattern in patterns:
            if pattern.pattern_type == PatternType.DAILY and pattern.confidence_score > 0.8:
                peak_hours = pattern.pattern_data.get("peak_hours", [])
                if peak_hours:
                    insights.append(AnalyticsInsightOut(
                        insight_type="usage_pattern",
                        title="Daily Usage Pattern Identified",
                        description=f"Your peak usage occurs during hours {', '.join(map(str, peak_hours))}.",
                        metrics={"peak_hours": peak_hours},
                        recommendations=[
                            "Schedule important operations during off-peak hours",
                            "Consider time-based features for optimal performance"
                        ],
                        confidence=pattern.confidence_score,
                        created_at=datetime.utcnow()
                    ))
        
        # Churn risk insights
        churn_risk = await self.get_churn_risk(merchant_id)
        if churn_risk and churn_risk.risk_score > 0.7:
            insights.append(AnalyticsInsightOut(
                insight_type="churn_risk",
                title="High Churn Risk Detected",
                description=f"Analysis indicates a {churn_risk.risk_score:.1%} probability of churn.",
                metrics={"risk_score": float(churn_risk.risk_score)},
                recommendations=churn_risk.recommended_actions,
                confidence=churn_risk.confidence,
                created_at=datetime.utcnow()
            ))
        
        return insights
    
    # ========== Helper Methods ==========
    
    def _extract_feature_from_event(self, subject: str) -> str:
        """Extract feature name from event type"""
        if "selfie" in subject:
            return "selfie"
        elif "match" in subject:
            return "match"
        elif "sort" in subject:
            return "sort"
        else:
            return "unknown"
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to days"""
        if timeframe.endswith("d"):
            return int(timeframe[:-1])
        elif timeframe.endswith("w"):
            return int(timeframe[:-1]) * 7
        elif timeframe.endswith("m"):
            return int(timeframe[:-1]) * 30
        elif timeframe.endswith("y"):
            return int(timeframe[:-1]) * 365
        else:
            return 30  # default
    
    def _calculate_risk_level(self, risk_score: Decimal) -> str:
        """Calculate risk level from score"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _format_trend_data(self, analytics: List) -> List[Dict[str, Any]]:
        """Format analytics data for trend charts"""
        return [
            {
                "date": a.date.isoformat(),
                "credits": float(a.total_credits_consumed),
                "api_calls": a.api_calls,
                "users": a.unique_users
            }
            for a in analytics
        ]
    
    async def _check_usage_patterns(self, merchant_id: UUID, correlation_id: str):
        """Check for usage patterns and anomalies"""
        # This would trigger pattern detection service
        try:
            await self.pattern_service.detect_patterns(merchant_id)
        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}", extra={
                "merchant_id": str(merchant_id),
                "correlation_id": correlation_id
            })
    
    async def _process_trial_event(self, merchant_id: UUID, payload: Dict[str, Any], subject: str, correlation_id: str):
        """Process trial-related events"""
        # Implementation would create/update trial analytics
        pass
    
    async def _process_conversion_event(self, merchant_id: UUID, payload: Dict[str, Any], correlation_id: str):
        """Process conversion events"""
        # Implementation would update trial analytics with conversion data
        pass
    
    async def _update_session_metrics(self, merchant_id: UUID, payload: Dict[str, Any]):
        """Update session metrics from auth events"""
        # Implementation would update engagement metrics
        pass
    
    async def _update_session_duration(self, merchant_id: UUID, payload: Dict[str, Any]):
        """Update session duration metrics"""
        # Implementation would calculate and store session duration
        pass


