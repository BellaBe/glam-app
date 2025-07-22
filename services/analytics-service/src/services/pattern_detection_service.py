from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
import statistics
from shared.utils.logger import ServiceLogger
from ..repositories.analytics_repository import AnalyticsRepository
from ..repositories.analytics_repository import UsagePatternRepository
from ..models.enums import PatternType
from ..exceptions import AnalyticsError

class PatternDetectionService:
    """Service for detecting usage patterns and anomalies"""
    
    def __init__(
        self,
        usage_repo: AnalyticsRepository,
        pattern_repo: UsagePatternRepository,
        logger: ServiceLogger,
        config
    ):
        self.usage_repo = usage_repo
        self.pattern_repo = pattern_repo
        self.logger = logger
        self.config = config
    
    async def detect_patterns(self, merchant_id: UUID) -> List[Dict[str, Any]]:
        """Detect all pattern types for a merchant"""
        patterns = []
        
        try:
            # Detect daily patterns
            daily_pattern = await self._detect_daily_patterns(merchant_id)
            if daily_pattern:
                patterns.append(daily_pattern)
            
            # Detect weekly patterns
            weekly_pattern = await self._detect_weekly_patterns(merchant_id)
            if weekly_pattern:
                patterns.append(weekly_pattern)
            
            # Detect seasonal patterns
            seasonal_pattern = await self._detect_seasonal_patterns(merchant_id)
            if seasonal_pattern:
                patterns.append(seasonal_pattern)
            
            # Detect behavioral patterns
            behavioral_pattern = await self._detect_behavioral_patterns(merchant_id)
            if behavioral_pattern:
                patterns.append(behavioral_pattern)
            
            # Save detected patterns
            for pattern_data in patterns:
                await self._save_pattern(merchant_id, pattern_data)
            
        except Exception as e:
            self.logger.error(
                f"Pattern detection failed for merchant {merchant_id}: {e}",
                extra={"merchant_id": str(merchant_id)}
            )
            raise AnalyticsError(f"Pattern detection failed: {e}")
        
        return patterns
    
    async def detect_anomalies(self, merchant_id: UUID) -> List[Dict[str, Any]]:
        """Detect usage anomalies"""
        anomalies = []
        
        # Get recent usage data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        usage_data = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        
        if len(usage_data) < 7:  # Need at least a week of data
            return anomalies
        
        # Check for usage spikes
        credits_values = [float(u.total_credits_consumed) for u in usage_data]
        api_call_values = [u.api_calls for u in usage_data]
        
        # Detect credit consumption anomalies
        credit_anomalies = self._detect_statistical_anomalies(
            credits_values, 
            "credits_consumed",
            usage_data
        )
        anomalies.extend(credit_anomalies)
        
        # Detect API call anomalies
        api_anomalies = self._detect_statistical_anomalies(
            api_call_values,
            "api_calls", 
            usage_data
        )
        anomalies.extend(api_anomalies)
        
        # Detect feature usage anomalies
        feature_anomalies = await self._detect_feature_anomalies(usage_data)
        anomalies.extend(feature_anomalies)
        
        return anomalies
    
    async def _detect_daily_patterns(self, merchant_id: UUID) -> Optional[Dict[str, Any]]:
        """Detect daily usage patterns"""
        # Get last 30 days of data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        usage_data = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        
        if len(usage_data) < 14:  # Need at least 2 weeks
            return None
        
        # Analyze peak hours from feature usage data
        hour_usage = {}
        for usage in usage_data:
            if usage.peak_hour is not None:
                hour_usage[usage.peak_hour] = hour_usage.get(usage.peak_hour, 0) + 1
        
        if not hour_usage:
            return None
        
        # Find consistently busy hours (appear in >60% of days)
        total_days = len(usage_data)
        threshold = total_days * 0.6
        peak_hours = [hour for hour, count in hour_usage.items() if count >= threshold]
        
        if not peak_hours:
            return None
        
        # Find low usage hours (opposite pattern)
        all_hours = set(range(24))
        busy_hours = set(peak_hours)
        low_hours = list(all_hours - busy_hours)[:4]  # Top 4 low hours
        
        confidence = min(max(hour_usage.values()) / total_days, 1.0)
        
        return {
            "type": PatternType.DAILY,
            "data": {
                "peak_hours": sorted(peak_hours),
                "low_hours": sorted(low_hours),
                "sample_days": total_days
            },
            "confidence": confidence,
            "strength": len(peak_hours) / 24  # Proportion of day that's predictable
        }
    
    async def _detect_weekly_patterns(self, merchant_id: UUID) -> Optional[Dict[str, Any]]:
        """Detect weekly usage patterns"""
        # Get last 8 weeks of data
        end_date = date.today()
        start_date = end_date - timedelta(weeks=8)
        usage_data = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        
        if len(usage_data) < 28:  # Need at least 4 weeks
            return None
        
        # Group by day of week
        weekday_usage = {}
        for usage in usage_data:
            weekday = usage.date.strftime("%A").lower()
            if weekday not in weekday_usage:
                weekday_usage[weekday] = []
            weekday_usage[weekday].append(float(usage.total_credits_consumed))
        
        # Calculate average usage per weekday
        weekday_averages = {}
        for day, values in weekday_usage.items():
            if values:
                weekday_averages[day] = statistics.mean(values)
        
        if len(weekday_averages) < 7:
            return None
        
        # Find peak and low days
        sorted_days = sorted(weekday_averages.items(), key=lambda x: x[1], reverse=True)
        peak_days = [day for day, _ in sorted_days[:3]]  # Top 3 days
        low_days = [day for day, _ in sorted_days[-2:]]  # Bottom 2 days
        
        # Calculate confidence based on consistency
        total_avg = statistics.mean(weekday_averages.values())
        max_avg = max(weekday_averages.values())
        confidence = min((max_avg - total_avg) / total_avg, 1.0) if total_avg > 0 else 0
        
        return {
            "type": PatternType.WEEKLY,
            "data": {
                "peak_days": peak_days,
                "low_days": low_days,
                "weekday_averages": weekday_averages,
                "sample_weeks": len(usage_data) // 7
            },
            "confidence": confidence,
            "strength": confidence
        }
    
    async def _detect_seasonal_patterns(self, merchant_id: UUID) -> Optional[Dict[str, Any]]:
        """Detect seasonal usage patterns"""
        # Get last 6 months of data
        end_date = date.today()
        start_date = end_date - timedelta(days=180)
        usage_data = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        
        if len(usage_data) < 90:  # Need at least 3 months
            return None
        
        # Group by month
        monthly_usage = {}
        for usage in usage_data:
            month = usage.date.strftime("%B").lower()
            if month not in monthly_usage:
                monthly_usage[month] = []
            monthly_usage[month].append(float(usage.total_credits_consumed))
        
        # Calculate monthly averages
        monthly_averages = {}
        for month, values in monthly_usage.items():
            if values:
                monthly_averages[month] = statistics.mean(values)
        
        if len(monthly_averages) < 3:
            return None
        
        # Identify high and low seasons
        sorted_months = sorted(monthly_averages.items(), key=lambda x: x[1], reverse=True)
        high_season = sorted_months[0][0]
        low_season = sorted_months[-1][0]
        
        high_usage = sorted_months[0][1]
        low_usage = sorted_months[-1][1]
        
        if low_usage > 0:
            usage_multiplier = high_usage / low_usage
        else:
            usage_multiplier = float('inf')
        
        # Confidence based on variation
        if len(monthly_averages) > 1:
            variance = statistics.variance(monthly_averages.values())
            mean_usage = statistics.mean(monthly_averages.values())
            confidence = min(variance / (mean_usage ** 2), 1.0) if mean_usage > 0 else 0
        else:
            confidence = 0
        
        return {
            "type": PatternType.SEASONAL,
            "data": {
                "high_season": high_season,
                "low_season": low_season,
                "usage_multiplier": usage_multiplier,
                "monthly_averages": monthly_averages
            },
            "confidence": confidence,
            "strength": min(usage_multiplier / 2.0, 1.0) if usage_multiplier != float('inf') else 1.0
        }
    
    async def _detect_behavioral_patterns(self, merchant_id: UUID) -> Optional[Dict[str, Any]]:
        """Detect behavioral usage patterns"""
        # Get last 30 days of data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        usage_data = await self.usage_repo.find_usage_trends(merchant_id, start_date, end_date)
        
        if len(usage_data) < 7:
            return None
        
        # Calculate usage metrics
        total_credits = sum(float(u.total_credits_consumed) for u in usage_data)
        total_api_calls = sum(u.api_calls for u in usage_data)
        active_days = len([u for u in usage_data if u.total_credits_consumed > 0])
        
        # Analyze feature usage patterns
        feature_usage = {}
        for usage in usage_data:
            for feature, data in usage.feature_usage.items():
                if feature not in feature_usage:
                    feature_usage[feature] = {"requests": 0, "credits": 0}
                if isinstance(data, dict):
                    feature_usage[feature]["requests"] += data.get("requests", 0)
                    feature_usage[feature]["credits"] += data.get("credits", 0)
        
        # Determine user type based on usage patterns
        avg_daily_credits = total_credits / len(usage_data) if len(usage_data) > 0 else 0
        usage_consistency = active_days / len(usage_data) if len(usage_data) > 0 else 0
        
        user_type = "casual_user"
        if avg_daily_credits > 100 and usage_consistency > 0.8:
            user_type = "power_user"
        elif avg_daily_credits > 50 or usage_consistency > 0.6:
            user_type = "regular_user"
        
        # Identify primary features
        primary_features = []
        if feature_usage:
            sorted_features = sorted(
                feature_usage.items(), 
                key=lambda x: x[1]["requests"], 
                reverse=True
            )
            primary_features = [f[0] for f in sorted_features[:3]]
        
        confidence = min(usage_consistency * 0.7 + (len(primary_features) / 3) * 0.3, 1.0)
        
        return {
            "type": PatternType.BEHAVIORAL,
            "data": {
                "user_type": user_type,
                "features": primary_features,
                "avg_daily_credits": avg_daily_credits,
                "usage_consistency": usage_consistency,
                "active_days_ratio": usage_consistency
            },
            "confidence": confidence,
            "strength": usage_consistency
        }
    
    def _detect_statistical_anomalies(
        self, 
        values: List[float], 
        metric_name: str, 
        usage_data: List
    ) -> List[Dict[str, Any]]:
        """Detect statistical anomalies in time series data"""
        if len(values) < 7:
            return []
        
        anomalies = []
        mean_val = statistics.mean(values)
        
        if len(values) > 1:
            stdev = statistics.stdev(values)
        else:
            return []
        
        if stdev == 0:
            return []
        
        # Z-score threshold for anomaly detection
        threshold = self.config.anomaly_detection_sensitivity * 2  # ~95% confidence
        
        for i, (value, usage) in enumerate(zip(values, usage_data)):
            z_score = abs(value - mean_val) / stdev
            
            if z_score > threshold:
                anomaly_type = "spike" if value > mean_val else "drop"
                severity = "high" if z_score > 3 else "medium"
                
                anomalies.append({
                    "type": "statistical_anomaly",
                    "anomaly_type": anomaly_type,
                    "date": usage.date.isoformat(),
                    "metric_name": metric_name,
                    "value": value,
                    "expected_range": {
                        "mean": mean_val,
                        "std_dev": stdev,
                        "z_score": z_score
                    },
                    "severity": severity,
                    "confidence": min(z_score / 3, 1.0)
                })
        
        return anomalies
    
    async def _detect_feature_anomalies(self, usage_data: List) -> List[Dict[str, Any]]:
        """Detect anomalies in feature usage patterns"""
        anomalies = []
        
        # Track feature usage over time
        feature_trends = {}
        for usage in usage_data:
            for feature, data in usage.feature_usage.items():
                if feature not in feature_trends:
                    feature_trends[feature] = []
                
                if isinstance(data, dict):
                    requests = data.get("requests", 0)
                    feature_trends[feature].append(requests)
        
        # Detect anomalies in each feature
        for feature, values in feature_trends.items():
            if len(values) < 7:
                continue
            
            feature_anomalies = self._detect_statistical_anomalies(
                values, f"feature_{feature}", usage_data[-len(values):]
            )
            
            for anomaly in feature_anomalies:
                anomaly["affected_features"] = [feature]
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _save_pattern(self, merchant_id: UUID, pattern_data: Dict[str, Any]) -> None:
        """Save detected pattern to database"""
        from ..models.analytics import UsagePattern
        
        # Check if similar pattern already exists
        existing_patterns = await self.pattern_repo.find_by_merchant_and_type(
            merchant_id, pattern_data["type"]
        )
        
        # Remove old patterns of the same type
        for pattern in existing_patterns:
            await self.pattern_repo.delete(pattern)
        
        # Create new pattern
        pattern = UsagePattern(
            merchant_id=merchant_id,
            merchant_domain="",  # Would be populated from merchant service
            pattern_type=pattern_data["type"],
            pattern_data=pattern_data["data"],
            confidence_score=Decimal(str(pattern_data["confidence"])),
            pattern_strength=Decimal(str(pattern_data["strength"])),
            sample_size=len(pattern_data["data"]) if isinstance(pattern_data["data"], (list, dict)) else 1,
            detected_at=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        
        await self.pattern_repo.save(pattern)


