from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from shared.utils.logger import ServiceLogger
from ..repositories.alert_repository import AlertRuleRepository, AlertHistoryRepository
from ..mappers.analytics_mapper import AlertRuleMapper, AlertHistoryMapper
from ..schemas.analytics import (
    AlertRuleIn, AlertRulePatch, AlertRuleOut,
    AlertHistoryPatch, AlertHistoryOut
)
from ..events.publishers import AnalyticsEventPublisher
from ..events.types import AnalyticsEvents
from ..exceptions import AlertError, AlertNotFoundError
from ..models.enums import AlertType, AlertSeverity, AlertStatus, ThresholdOperator

class AlertService:
    """Service for managing alerts and notifications"""
    
    def __init__(
        self,
        rule_repo: AlertRuleRepository,
        history_repo: AlertHistoryRepository,
        rule_mapper: AlertRuleMapper,
        history_mapper: AlertHistoryMapper,
        publisher: AnalyticsEventPublisher,
        logger: ServiceLogger,
        config
    ):
        self.rule_repo = rule_repo
        self.history_repo = history_repo
        self.rule_mapper = rule_mapper
        self.history_mapper = history_mapper
        self.publisher = publisher
        self.logger = logger
        self.config = config
    
    # ========== Alert Rule Management ==========
    
    async def create_alert_rule(self, merchant_id: UUID, dto: AlertRuleIn) -> AlertRuleOut:
        """Create new alert rule"""
        self.logger.info(f"Creating alert rule: {dto.rule_name}")
        
        # Validate rule configuration
        await self._validate_alert_rule(dto)
        
        # Convert DTO to model and save
        model = self.rule_mapper.to_model(dto, merchant_id=merchant_id)
        await self.rule_repo.save(model)
        
        # Return DTO
        result = self.rule_mapper.to_out(model)
        
        self.logger.info(
            "Created alert rule",
            extra={
                "rule_id": str(model.id),
                "merchant_id": str(merchant_id),
                "alert_type": dto.alert_type,
                "rule_name": dto.rule_name
            }
        )
        
        return result
    
    async def get_alert_rule(self, rule_id: UUID) -> AlertRuleOut:
        """Get alert rule by ID"""
        model = await self.rule_repo.find_by_id(rule_id)
        if not model:
            raise AlertNotFoundError(f"Alert rule {rule_id} not found")
        return self.rule_mapper.to_out(model)
    
    async def list_alert_rules(self, merchant_id: UUID) -> List[AlertRuleOut]:
        """List alert rules for merchant"""
        rules = await self.rule_repo.find_active_rules(merchant_id)
        return self.rule_mapper.list_to_out(rules)
    
    async def update_alert_rule(self, rule_id: UUID, patch: AlertRulePatch) -> AlertRuleOut:
        """Update alert rule"""
        model = await self.rule_repo.find_by_id(rule_id)
        if not model:
            raise AlertNotFoundError(f"Alert rule {rule_id} not found")
        
        # Apply patch using mapper
        self.rule_mapper.patch_model(model, patch)
        await self.rule_repo.save(model)
        
        return self.rule_mapper.to_out(model)
    
    async def delete_alert_rule(self, rule_id: UUID) -> None:
        """Delete alert rule"""
        model = await self.rule_repo.find_by_id(rule_id)
        if not model:
            raise AlertNotFoundError(f"Alert rule {rule_id} not found")
        
        await self.rule_repo.delete(model)
        self.logger.info(f"Deleted alert rule: {rule_id}")
    
    async def test_alert_rule(self, rule_id: UUID, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test alert rule without triggering notifications"""
        rule = await self.rule_repo.find_by_id(rule_id)
        if not rule:
            raise AlertNotFoundError(f"Alert rule {rule_id} not found")
        
        # Simulate rule evaluation
        metric_value = Decimal(str(test_data.get("metric_value", 0)))
        threshold_met = self._evaluate_threshold(
            metric_value,
            rule.threshold_value,
            rule.threshold_operator
        )
        
        return {
            "rule_id": str(rule_id),
            "rule_name": rule.rule_name,
            "threshold_met": threshold_met,
            "metric_value": float(metric_value),
            "threshold_value": float(rule.threshold_value),
            "operator": rule.threshold_operator,
            "would_trigger": threshold_met and rule.is_active,
            "test_timestamp": datetime.utcnow().isoformat()
        }
    
    # ========== Alert Processing ==========
    
    async def evaluate_alerts(self, merchant_id: UUID, metrics: Dict[str, Any]) -> List[str]:
        """Evaluate all active alert rules for merchant"""
        rules = await self.rule_repo.find_active_rules(merchant_id)
        triggered_alerts = []
        
        for rule in rules:
            try:
                if await self._should_trigger_alert(rule, metrics):
                    alert_id = await self._trigger_alert(rule, metrics)
                    triggered_alerts.append(str(alert_id))
            except Exception as e:
                self.logger.error(
                    f"Error evaluating alert rule {rule.id}: {e}",
                    extra={"rule_id": str(rule.id), "merchant_id": str(merchant_id)}
                )
        
        return triggered_alerts
    
    async def acknowledge_alert(self, alert_id: UUID, acknowledged_by: str) -> AlertHistoryOut:
        """Acknowledge an active alert"""
        alert = await self.history_repo.find_by_id(alert_id)
        if not alert:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        
        if alert.status != AlertStatus.ACTIVE:
            raise AlertError(f"Alert {alert_id} is not active")
        
        patch = AlertHistoryPatch(
            status=AlertStatus.ACKNOWLEDGED,
            resolved_by=acknowledged_by
        )
        
        self.history_mapper.patch_model(alert, patch)
        await self.history_repo.save(alert)
        
        self.logger.info(
            "Alert acknowledged",
            extra={
                "alert_id": str(alert_id),
                "acknowledged_by": acknowledged_by,
                "merchant_id": str(alert.merchant_id)
            }
        )
        
        return self.history_mapper.to_out(alert)
    
    async def resolve_alert(
        self, 
        alert_id: UUID, 
        resolved_by: str, 
        resolution_notes: Optional[str] = None
    ) -> AlertHistoryOut:
        """Resolve an alert"""
        alert = await self.history_repo.find_by_id(alert_id)
        if not alert:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        
        patch = AlertHistoryPatch(
            status=AlertStatus.RESOLVED,
            resolved_by=resolved_by,
            resolution_notes=resolution_notes
        )
        
        self.history_mapper.patch_model(alert, patch)
        alert.resolved_at = datetime.utcnow()
        await self.history_repo.save(alert)
        
        # Publish alert resolved event
        await self.publisher.publish_event(
            AnalyticsEvents.ALERT_RESOLVED,
            {
                "alert_id": str(alert_id),
                "merchant_id": str(alert.merchant_id),
                "alert_type": alert.alert_type,
                "resolved_by": resolved_by,
                "resolution_notes": resolution_notes
            }
        )
        
        self.logger.info(
            "Alert resolved",
            extra={
                "alert_id": str(alert_id),
                "resolved_by": resolved_by,
                "merchant_id": str(alert.merchant_id)
            }
        )
        
        return self.history_mapper.to_out(alert)
    
    # ========== Alert History ==========
    
    async def get_alert_history(
        self, 
        merchant_id: UUID,
        status: Optional[AlertStatus] = None,
        limit: int = 50
    ) -> List[AlertHistoryOut]:
        """Get alert history for merchant"""
        alerts = await self.history_repo.find_by_merchant(merchant_id, status, limit)
        return self.history_mapper.list_to_out(alerts)
    
    async def get_active_alerts(self, merchant_id: UUID) -> List[AlertHistoryOut]:
        """Get active alerts for merchant"""
        alerts = await self.history_repo.find_active_alerts(merchant_id)
        return self.history_mapper.list_to_out(alerts)
    
    async def get_alert_history_by_id(self, alert_id: UUID) -> AlertHistoryOut:
        """Get specific alert from history"""
        alert = await self.history_repo.find_by_id(alert_id)
        if not alert:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        return self.history_mapper.to_out(alert)
    
    # ========== Alert Templates ==========
    
    async def get_alert_templates(self) -> List[Dict[str, Any]]:
        """Get pre-configured alert templates"""
        return [
            {
                "name": "Credit Low Warning",
                "alert_type": AlertType.CREDIT_LOW,
                "description": "Alert when credit balance is running low",
                "metric_name": "credits_remaining",
                "threshold_operator": ThresholdOperator.LESS_THAN,
                "suggested_threshold": 100,
                "severity": AlertSeverity.MEDIUM,
                "notification_channels": {
                    "email": {"enabled": True},
                    "dashboard": {"enabled": True}
                }
            },
            {
                "name": "Order Limit Critical",
                "alert_type": AlertType.ORDER_LIMIT_LOW,
                "description": "Alert when order limit is nearly exceeded",
                "metric_name": "order_limit_remaining",
                "threshold_operator": ThresholdOperator.LESS_THAN,
                "suggested_threshold": 10,
                "severity": AlertSeverity.HIGH,
                "notification_channels": {
                    "email": {"enabled": True},
                    "webhook": {"enabled": True},
                    "dashboard": {"enabled": True}
                }
            },
            {
                "name": "High Churn Risk",
                "alert_type": AlertType.CHURN_RISK,
                "description": "Alert when churn risk probability is high",
                "metric_name": "churn_probability",
                "threshold_operator": ThresholdOperator.GREATER_THAN,
                "suggested_threshold": 0.7,
                "severity": AlertSeverity.HIGH,
                "notification_channels": {
                    "email": {"enabled": True},
                    "dashboard": {"enabled": True}
                }
            },
            {
                "name": "Trial Expiring Soon",
                "alert_type": AlertType.TRIAL_EXPIRING,
                "description": "Alert when trial period is ending",
                "metric_name": "days_until_trial_end",
                "threshold_operator": ThresholdOperator.LESS_THAN_EQUAL,
                "suggested_threshold": 3,
                "severity": AlertSeverity.MEDIUM,
                "notification_channels": {
                    "email": {"enabled": True},
                    "dashboard": {"enabled": True}
                }
            },
            {
                "name": "Usage Spike Detection",
                "alert_type": AlertType.USAGE_SPIKE,
                "description": "Alert when usage increases dramatically",
                "metric_name": "usage_growth_percentage",
                "threshold_operator": ThresholdOperator.GREATER_THAN,
                "suggested_threshold": 200,  # 200% increase
                "severity": AlertSeverity.MEDIUM,
                "notification_channels": {
                    "email": {"enabled": True},
                    "dashboard": {"enabled": True}
                }
            }
        ]
    
    # ========== Private Methods ==========
    
    async def _validate_alert_rule(self, dto: AlertRuleIn) -> None:
        """Validate alert rule configuration"""
        # Validate threshold value based on metric type
        if dto.threshold_value < 0:
            raise AlertError("Threshold value cannot be negative")
        
        # Validate cooldown period
        if dto.cooldown_minutes < 1 or dto.cooldown_minutes > 1440:  # 1 minute to 24 hours
            raise AlertError("Cooldown period must be between 1 and 1440 minutes")
        
        # Validate notification channels
        if not dto.notification_channels:
            raise AlertError("At least one notification channel must be configured")
    
    async def _should_trigger_alert(self, rule, metrics: Dict[str, Any]) -> bool:
        """Check if alert rule should trigger"""
        # Check if rule is active
        if not rule.is_active:
            return False
        
        # Check cooldown period
        if await self.rule_repo.check_cooldown(rule.id, rule.cooldown_minutes):
            return False
        
        # Check daily alert limit
        today = datetime.utcnow()
        daily_count = await self.history_repo.count_daily_alerts(rule.id, today)
        if daily_count >= rule.max_alerts_per_day:
            return False
        
        # Check threshold condition
        metric_value = metrics.get(rule.metric_name)
        if metric_value is None:
            return False
        
        return self._evaluate_threshold(
            Decimal(str(metric_value)),
            rule.threshold_value,
            rule.threshold_operator
        )
    
    def _evaluate_threshold(
        self, 
        metric_value: Decimal, 
        threshold_value: Decimal, 
        operator: ThresholdOperator
    ) -> bool:
        """Evaluate threshold condition"""
        if operator == ThresholdOperator.LESS_THAN:
            return metric_value < threshold_value
        elif operator == ThresholdOperator.GREATER_THAN:
            return metric_value > threshold_value
        elif operator == ThresholdOperator.LESS_THAN_EQUAL:
            return metric_value <= threshold_value
        elif operator == ThresholdOperator.GREATER_THAN_EQUAL:
            return metric_value >= threshold_value
        elif operator == ThresholdOperator.EQUAL:
            return metric_value == threshold_value
        else:
            return False
    
    async def _trigger_alert(self, rule, metrics: Dict[str, Any]) -> UUID:
        """Trigger an alert and create history record"""
        from ..models.analytics import AlertHistory
        
        metric_value = Decimal(str(metrics[rule.metric_name]))
        
        # Create alert history record
        alert = AlertHistory(
            alert_rule_id=rule.id,
            merchant_id=rule.merchant_id,
            merchant_domain=metrics.get("merchant_domain", ""),
            alert_type=rule.alert_type,
            severity=rule.severity,
            metric_name=rule.metric_name,
            metric_value=metric_value,
            threshold_value=rule.threshold_value,
            alert_message=self._generate_alert_message(rule, metric_value),
            context_data={"metrics": metrics},
            status=AlertStatus.ACTIVE,
            triggered_at=datetime.utcnow()
        )
        
        await self.history_repo.save(alert)
        
        # Update rule last triggered time and count
        rule.last_triggered = datetime.utcnow()
        rule.trigger_count += 1
        await self.rule_repo.save(rule)
        
        # Publish alert event
        await self.publisher.publish_event(
            AnalyticsEvents.ALERT_TRIGGERED,
            {
                "alert_id": str(alert.id),
                "merchant_id": str(rule.merchant_id),
                "alert_type": rule.alert_type,
                "severity": rule.severity,
                "metric_name": rule.metric_name,
                "metric_value": float(metric_value),
                "threshold_value": float(rule.threshold_value),
                "alert_message": alert.alert_message
            }
        )
        
        # Send notifications (would integrate with notification service)
        await self._send_notifications(rule, alert)
        
        self.logger.info(
            "Alert triggered",
            extra={
                "alert_id": str(alert.id),
                "rule_id": str(rule.id),
                "merchant_id": str(rule.merchant_id),
                "alert_type": rule.alert_type,
                "metric_value": float(metric_value)
            }
        )
        
        return alert.id
    
    def _generate_alert_message(self, rule, metric_value: Decimal) -> str:
        """Generate human-readable alert message"""
        return (
            f"Alert: {rule.rule_name} - "
            f"{rule.metric_name} is {metric_value} "
            f"(threshold: {rule.threshold_operator} {rule.threshold_value})"
        )
    
    async def _send_notifications(self, rule, alert) -> None:
        """Send notifications for triggered alert"""
        # This would integrate with a notification service
        # For now, just log the notification attempt
        channels = rule.notification_channels
        
        if channels.get("email", {}).get("enabled", False):
            self.logger.info(f"Would send email notification for alert {alert.id}")
        
        if channels.get("webhook", {}).get("enabled", False):
            self.logger.info(f"Would send webhook notification for alert {alert.id}")
        
        if channels.get("dashboard", {}).get("enabled", False):
            self.logger.info(f"Would show dashboard notification for alert {alert.id}")


