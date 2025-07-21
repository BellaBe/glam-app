# services/billing-service/src/mappers/subscription_mapper.py
"""Mapper for subscription model to response schemas."""

from shared.mappers.crud_mapper import CRUDMapper

from ..models import Subscription, BillingPlan
from ..schemas.subscription import SubscriptionIn, SubscriptionPatch, SubscriptionOut, SubscriptionCreateOut
from ..mappers import BillingPlanMapper
    
class SubscriptionMapper(CRUDMapper[
    Subscription, SubscriptionIn, SubscriptionPatch, SubscriptionOut
]):
    model_cls = Subscription
    out_schema = SubscriptionOut
    
    @staticmethod
    def to_create_out(subscription: Subscription, plan: BillingPlan, url: str) -> SubscriptionCreateOut:
        return SubscriptionCreateOut(
            subscription_id=subscription.id,
            confirmation_url=url,
            status=subscription.status,
            plan_details=BillingPlanMapper().to_out(plan),
        )