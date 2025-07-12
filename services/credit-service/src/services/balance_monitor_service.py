# services/credit-service/src/services/balance_monitor_service.py
"""Service for monitoring credit balance thresholds."""

from uuid import UUID
from typing import Optional

from shared.utils.logger import ServiceLogger

from ..config import ServiceConfig
from ..events.publishers import CreditEventPublisher
from ..metrics import increment_event_published


class BalanceMonitorService:
    """Monitors credit balance changes and publishes threshold events"""
    
    def __init__(
        self,
        config: ServiceConfig,
        publisher: CreditEventPublisher,
        logger: ServiceLogger
    ):
        self.config = config
        self.publisher = publisher
        self.logger = logger
        
        # Calculate threshold
        self.low_threshold = (
            self.config.TRIAL_CREDITS * 
            self.config.LOW_BALANCE_THRESHOLD_PERCENT / 100
        )
    
    async def check_balance_thresholds(
        self,
        merchant_id: UUID,
        old_balance: int,
        new_balance: int,
        correlation_id: Optional[str] = None
    ) -> None:
        """Check if balance crosses any thresholds and publish events"""
        
        try:
            # Low balance crossed downward
            if old_balance > self.low_threshold and new_balance <= self.low_threshold:
                await self.publisher.publish_low_balance_reached(
                    merchant_id=merchant_id,
                    balance=new_balance,
                    threshold=self.low_threshold,
                    correlation_id=correlation_id
                )
                increment_event_published("low_balance_reached")
                
                self.logger.warning(
                    "Low balance threshold reached",
                    merchant_id=str(merchant_id),
                    balance=float(new_balance),
                    threshold=float(self.low_threshold)
                )
            
            # Balance restored
            elif old_balance <= self.low_threshold and new_balance > self.low_threshold:
                await self.publisher.publish_balance_restored(
                    merchant_id=merchant_id,
                    balance=new_balance,
                    correlation_id=correlation_id
                )
                increment_event_published("balance_restored")
                
                self.logger.info(
                    "Balance restored above threshold",
                    merchant_id=str(merchant_id),
                    balance=float(new_balance),
                    threshold=float(self.low_threshold)
                )
            
            # Balance exhausted
            if old_balance > 0 and new_balance == 0:
                await self.publisher.publish_balance_exhausted(
                    merchant_id=merchant_id,
                    correlation_id=correlation_id
                )
                increment_event_published("balance_exhausted")
                
                self.logger.warning(
                    "Balance exhausted",
                    merchant_id=str(merchant_id)
                )
            
            # Plugin status change
            if (old_balance > 0 and new_balance == 0) or (old_balance == 0 and new_balance > 0):
                previous_status = "disabled" if new_balance > 0 else "enabled"
                current_status = "enabled" if new_balance > 0 else "disabled"
                reason = "Sufficient credits" if new_balance > 0 else "Insufficient credits"
                
                await self.publisher.publish_plugin_status_changed(
                    merchant_id=merchant_id,
                    previous_status=previous_status,
                    current_status=current_status,
                    reason=reason,
                    balance=new_balance,
                    correlation_id=correlation_id
                )
                increment_event_published("plugin_status_changed")
                
                self.logger.info(
                    "Plugin status changed",
                    merchant_id=str(merchant_id),
                    previous_status=previous_status,
                    current_status=current_status,
                    balance=float(new_balance)
                )
                
        except Exception as e:
            self.logger.error(
                "Failed to check balance thresholds",
                merchant_id=str(merchant_id),
                old_balance=float(old_balance),
                new_balance=float(new_balance),
                error=str(e),
                exc_info=True
            )
            # Don't re-raise - threshold checking is not critical for transaction success