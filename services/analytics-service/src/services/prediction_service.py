from uuid import UUID
from typing import Dict, Any, Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
import random  # In production, replace with actual ML models
from shared.utils.logger import ServiceLogger
from ..repositories.analytics_repository import AnalyticsRepository, OrderAnalyticsRepository, LifecycleTrialAnalyticsRepository
from ..repositories.analytics_repository import PredictionModelRepository
from ..mappers.analytics_mapper import PredictionModelMapper
from ..schemas.analytics import PredictionModelIn, ChurnRiskOut
from ..models.enums import PredictionType
from ..exceptions import PredictionError

class PredictionService:
    """Service for generating ML predictions and forecasts"""
    
    def __init__(
        self,
        usage_repo: AnalyticsRepository,
        order_repo: OrderAnalyticsRepository,
        trial_repo: LifecycleTrialAnalyticsRepository,
        prediction_repo: PredictionModelRepository,
        prediction_mapper: PredictionModelMapper,
        logger: ServiceLogger,
        config
    ):
        self.usage_repo = usage_repo
        self.order_repo = order_repo
        self.trial_repo = trial_repo
        self.prediction_repo = prediction_repo
        self.prediction_mapper = prediction_mapper
        self.logger = logger
        self.config = config
    
    async def predict_churn_risk(self, merchant_id: UUID) -> ChurnRiskOut:
        """Predict churn risk for merchant"""
        # Get historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        usage_history = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        
        if not usage_history:
            # No data available for prediction
            return ChurnRiskOut(
                merchant_id=merchant_id,
                risk_score=Decimal("0.5"),
                risk_level="medium",
                factors=[],
                recommended_actions=["Increase platform engagement", "Contact customer success"],
                predicted_churn_date=None,
                confidence=Decimal("0.3")
            )
        
        # Extract features for prediction
        features = self._extract_churn_features(usage_history)
        
        # Generate prediction (in production, use trained ML model)
        risk_score = self._calculate_churn_risk(features)
        
        # Determine risk factors
        risk_factors = self._identify_risk_factors(features)
        
        # Generate recommendations
        recommendations = self._generate_churn_recommendations(risk_factors, risk_score)
        
        # Calculate predicted churn date
        predicted_date = None
        if risk_score > 0.7:
            days_to_churn = int((1 - risk_score) * 90)  # Simplified calculation
            predicted_date = date.today() + timedelta(days=days_to_churn)
        
        # Save prediction
        prediction_data = PredictionModelIn(
            prediction_type=PredictionType.CHURN_RISK,
            prediction_date=date.today(),
            prediction_value=risk_score,
            factors={
                "risk_factors": [f["factor"] for f in risk_factors],
                "feature_scores": features,
                "recommendations": recommendations
            },
            model_version="churn_v1.0"
        )
        
        model = self.prediction_mapper.to_model(prediction_data, merchant_id=merchant_id)
        await self.prediction_repo.save(model)
        
        return ChurnRiskOut(
            merchant_id=merchant_id,
            risk_score=risk_score,
            risk_level=self._calculate_risk_level(risk_score),
            factors=risk_factors,
            recommended_actions=recommendations,
            predicted_churn_date=predicted_date,
            confidence=Decimal(str(self.config.prediction_confidence_level))
        )
    
    async def predict_credit_depletion(self, merchant_id: UUID) -> Dict[str, Any]:
        """Predict when merchant will run out of credits"""
        # Get recent usage data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        usage_history = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        
        if not usage_history:
            return {
                "prediction_date": None,
                "days_remaining": None,
                "confidence": 0.3,
                "usage_trend": "insufficient_data"
            }
        
        # Calculate daily usage trend
        daily_usage = [float(u.total_credits_consumed) for u in usage_history]
        avg_daily_usage = sum(daily_usage) / len(daily_usage) if daily_usage else 0
        
        # Get current credit balance (would come from credits service)
        # For now, simulate based on recent usage
        estimated_balance = avg_daily_usage * 30  # Rough estimate
        
        if avg_daily_usage <= 0:
            return {
                "prediction_date": None,
                "days_remaining": None,
                "confidence": 0.8,
                "usage_trend": "no_usage"
            }
        
        # Calculate depletion date
        days_remaining = int(estimated_balance / avg_daily_usage)
        predicted_date = date.today() + timedelta(days=days_remaining)
        
        # Calculate confidence based on usage consistency
        if len(daily_usage) > 1:
            import statistics
            usage_variance = statistics.variance(daily_usage)
            avg_usage = statistics.mean(daily_usage)
            consistency = 1 - min(usage_variance / (avg_usage ** 2), 1) if avg_usage > 0 else 0
        else:
            consistency = 0.5
        
        # Save prediction
        prediction_data = PredictionModelIn(
            prediction_type=PredictionType.CREDIT_DEPLETION,
            prediction_date=predicted_date,
            prediction_value=Decimal(str(days_remaining)),
            factors={
                "avg_daily_usage": avg_daily_usage,
                "estimated_balance": estimated_balance,
                "usage_consistency": consistency,
                "trend": "stable" if consistency > 0.7 else "variable"
            },
            model_version="credit_depletion_v1.0"
        )
        
        model = self.prediction_mapper.to_model(prediction_data, merchant_id=merchant_id)
        await self.prediction_repo.save(model)
        
        return {
            "prediction_date": predicted_date,
            "days_remaining": days_remaining,
            "confidence": consistency,
            "usage_trend": "stable" if consistency > 0.7 else "variable",
            "avg_daily_usage": avg_daily_usage,
            "estimated_balance": estimated_balance
        }
    
    async def predict_trial_conversion(self, merchant_id: UUID) -> Dict[str, Any]:
        """Predict trial conversion probability"""
        trial_data = await self.trial_repo.find_by_merchant(merchant_id)
        
        if not trial_data or trial_data.converted:
            return {
                "conversion_probability": 0.0,
                "factors": [],
                "recommendations": [],
                "confidence": 0.0
            }
        
        # Extract conversion features
        days_in_trial = (datetime.utcnow() - trial_data.trial_start_date).days
        days_remaining = max(0, trial_data.trial_duration_days - days_in_trial)
        
        # Calculate engagement score
        engagement_score = float(trial_data.trial_engagement_score)
        features_used = len(trial_data.features_used_during_trial)
        sessions_per_day = trial_data.total_sessions / max(days_in_trial, 1)
        
        # Simple conversion probability calculation (replace with trained model)
        probability = min(
            (engagement_score * 0.4 + 
             min(features_used / 3, 1) * 0.3 + 
             min(sessions_per_day / 2, 1) * 0.3),
            1.0
        )
        
        # Apply time decay if trial is ending
        if days_remaining < 7:
            probability *= (days_remaining / 7) * 0.8 + 0.2
        
        # Identify conversion factors
        factors = []
        if engagement_score > 0.7:
            factors.append({"factor": "high_engagement", "impact": "positive", "score": engagement_score})
        if features_used >= 2:
            factors.append({"factor": "feature_adoption", "impact": "positive", "score": features_used})
        if sessions_per_day < 0.5:
            factors.append({"factor": "low_activity", "impact": "negative", "score": sessions_per_day})
        if days_remaining < 3:
            factors.append({"factor": "trial_ending_soon", "impact": "negative", "score": days_remaining})
        
        # Generate recommendations
        recommendations = []
        if probability < 0.5:
            recommendations.append("Reach out with personalized onboarding")
            recommendations.append("Offer trial extension with incentive")
        if features_used < 2:
            recommendations.append("Encourage exploration of additional features")
        if sessions_per_day < 1:
            recommendations.append("Send engagement reminders")
        
        # Save prediction
        prediction_data = PredictionModelIn(
            prediction_type=PredictionType.TRIAL_CONVERSION,
            prediction_date=date.today(),
            prediction_value=Decimal(str(probability)),
            factors={
                "conversion_factors": factors,
                "recommendations": recommendations,
                "engagement_score": engagement_score,
                "features_used": features_used,
                "days_remaining": days_remaining
            },
            model_version="trial_conversion_v1.0"
        )
        
        model = self.prediction_mapper.to_model(prediction_data, merchant_id=merchant_id)
        await self.prediction_repo.save(model)
        
        return {
            "conversion_probability": probability,
            "factors": factors,
            "recommendations": recommendations,
            "confidence": 0.75,
            "days_remaining": days_remaining
        }
    
    async def predict_growth_forecast(self, merchant_id: UUID, horizon_days: int = 90) -> Dict[str, Any]:
        """Predict growth forecast for merchant"""
        # Get historical usage data
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        usage_history = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        
        if len(usage_history) < 30:
            return {
                "forecast": [],
                "growth_rate": 0.0,
                "confidence": 0.2,
                "trend": "insufficient_data"
            }
        
        # Calculate growth trend
        daily_usage = [float(u.total_credits_consumed) for u in usage_history]
        
        # Simple linear regression for trend (replace with sophisticated model)
        x_values = list(range(len(daily_usage)))
        n = len(daily_usage)
        
        if n > 1:
            sum_x = sum(x_values)
            sum_y = sum(daily_usage)
            sum_xy = sum(x * y for x, y in zip(x_values, daily_usage))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
        else:
            slope = 0
            intercept = daily_usage[0] if daily_usage else 0
        
        # Generate forecast
        forecast = []
        for days_ahead in range(1, horizon_days + 1):
            predicted_usage = max(0, intercept + slope * (len(daily_usage) + days_ahead))
            forecast_date = date.today() + timedelta(days=days_ahead)
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted_usage": predicted_usage,
                "confidence_lower": predicted_usage * 0.8,
                "confidence_upper": predicted_usage * 1.2
            })
        
        # Calculate overall growth rate
        if len(daily_usage) > 7:
            recent_avg = sum(daily_usage[-7:]) / 7
            older_avg = sum(daily_usage[:7]) / 7
            growth_rate = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        else:
            growth_rate = 0
        
        trend = "growing" if growth_rate > 5 else "declining" if growth_rate < -5 else "stable"
        
        # Save prediction
        prediction_data = PredictionModelIn(
            prediction_type=PredictionType.GROWTH_FORECAST,
            prediction_date=date.today(),
            prediction_value=Decimal(str(growth_rate)),
            factors={
                "slope": slope,
                "intercept": intercept,
                "horizon_days": horizon_days,
                "data_points": len(daily_usage)
            },
            model_version="growth_forecast_v1.0"
        )
        
        model = self.prediction_mapper.to_model(prediction_data, merchant_id=merchant_id)
        await self.prediction_repo.save(model)
        
        return {
            "forecast": forecast[:30],  # Return first 30 days
            "growth_rate": growth_rate,
            "confidence": 0.7,
            "trend": trend,
            "horizon_days": horizon_days
        }
    
    def _extract_churn_features(self, usage_history: List) -> Dict[str, float]:
        """Extract features for churn prediction"""
        if not usage_history:
            return {}
        
        # Calculate usage metrics
        daily_credits = [float(u.total_credits_consumed) for u in usage_history]
        daily_calls = [u.api_calls for u in usage_history]
        
        # Recent vs historical usage
        recent_usage = sum(daily_credits[-7:]) / 7 if len(daily_credits) >= 7 else 0
        historical_usage = sum(daily_credits[:-7]) / max(len(daily_credits) - 7, 1) if len(daily_credits) > 7 else recent_usage
        
        # Usage decline
        usage_decline = (historical_usage - recent_usage) / historical_usage if historical_usage > 0 else 0
        
        # Activity consistency
        active_days = len([u for u in usage_history if u.total_credits_consumed > 0])
        consistency = active_days / len(usage_history) if usage_history else 0
        
        # Feature diversity
        all_features = set()
        for usage in usage_history:
            all_features.update(usage.feature_usage.keys())
        feature_diversity = len(all_features)
        
        # Error rate
        total_errors = sum(u.error_count for u in usage_history)
        total_calls = sum(u.api_calls for u in usage_history)
        error_rate = total_errors / total_calls if total_calls > 0 else 0
        
        return {
            "usage_decline": usage_decline,
            "consistency": consistency,
            "feature_diversity": feature_diversity,
            "error_rate": error_rate,
            "recent_usage": recent_usage,
            "historical_usage": historical_usage,
            "active_days_ratio": consistency,
            "avg_daily_usage": sum(daily_credits) / len(daily_credits) if daily_credits else 0
        }
    
    def _calculate_churn_risk(self, features: Dict[str, float]) -> Decimal:
        """Calculate churn risk score (simplified model)"""
        if not features:
            return Decimal("0.5")
        
        # Weight factors for churn risk
        risk_score = (
            features.get("usage_decline", 0) * 0.3 +
            (1 - features.get("consistency", 1)) * 0.25 +
            features.get("error_rate", 0) * 0.2 +
            (1 - min(features.get("feature_diversity", 0) / 3, 1)) * 0.15 +
            (1 - min(features.get("avg_daily_usage", 0) / 50, 1)) * 0.1
        )
        
        return Decimal(str(min(max(risk_score, 0), 1)))
    
    def _identify_risk_factors(self, features: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify specific risk factors"""
        factors = []
        
        if features.get("usage_decline", 0) > 0.3:
            factors.append({
                "factor": "significant_usage_decline",
                "impact": "negative",
                "score": features["usage_decline"]
            })
        
        if features.get("consistency", 1) < 0.5:
            factors.append({
                "factor": "inconsistent_usage",
                "impact": "negative", 
                "score": 1 - features["consistency"]
            })
        
        if features.get("error_rate", 0) > 0.1:
            factors.append({
                "factor": "high_error_rate",
                "impact": "negative",
                "score": features["error_rate"]
            })
        
        if features.get("feature_diversity", 3) < 2:
            factors.append({
                "factor": "limited_feature_adoption",
                "impact": "negative",
                "score": 1 - features["feature_diversity"] / 3
            })
        
        return factors
    
    def _generate_churn_recommendations(self, risk_factors: List[Dict], risk_score: Decimal) -> List[str]:
        """Generate recommendations to reduce churn risk"""
        recommendations = []
        
        factor_types = {f["factor"] for f in risk_factors}
        
        if "significant_usage_decline" in factor_types:
            recommendations.extend([
                "Reach out to understand usage changes",
                "Offer training or support to re-engage",
                "Consider account health check"
            ])
        
        if "inconsistent_usage" in factor_types:
            recommendations.extend([
                "Send usage reminders and tips",
                "Offer workflow optimization consultation"
            ])
        
        if "high_error_rate" in factor_types:
            recommendations.extend([
                "Provide technical support",
                "Review API integration quality"
            ])
        
        if "limited_feature_adoption" in factor_types:
            recommendations.extend([
                "Demonstrate additional features",
                "Provide feature-specific training"
            ])
        
        if risk_score > 0.8:
            recommendations.insert(0, "Schedule immediate customer success intervention")
        elif risk_score > 0.6:
            recommendations.insert(0, "Prioritize for proactive outreach")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
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


