from datetime import datetime
from typing import Optional
import uuid7
from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects
from ..schemas.credit import (
    BalanceChangedEvent, BalanceLowEvent, BalanceDepletedEvent
)

class CreditEventPublisher(Publisher):
    """Publisher for credit-related events"""
    
    @property
    def service_name(self) -> str:
        return "credit-service"
    
    async def balance_changed(
        self,
        shop_domain: str,
        delta: int,
        new_balance: int,
        reason: str,
        external_ref: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish balance changed event"""
        payload = BalanceChangedEvent(
            shop_domain=shop_domain,
            delta=delta,
            new_balance=new_balance,
            reason=reason,
            external_ref=external_ref,
            at=datetime.utcnow()
        )
        
        return await self.publish_event(
            subject="evt.credit.balance.changed.v1",
            data=payload.model_dump(),
            correlation_id=correlation_id
        )
    
    async def balance_low(
        self,
        shop_domain: str,
        balance: int,
        threshold: int,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish low balance event"""
        payload = BalanceLowEvent(
            shop_domain=shop_domain,
            balance=balance,
            threshold=threshold,
            at=datetime.utcnow()
        )
        
        return await self.publish_event(
            subject="evt.credit.balance.low.v1",
            data=payload.model_dump(),
            correlation_id=correlation_id
        )
    
    async def balance_depleted(
        self,
        shop_domain: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish balance depleted event"""
        payload = BalanceDepletedEvent(
            shop_domain=shop_domain,
            at=datetime.utcnow()
        )
        
        return await self.publish_event(
            subject="evt.credit.balance.depleted.v1",
            data=payload.model_dump(),
            correlation_id=correlation_id
        )

