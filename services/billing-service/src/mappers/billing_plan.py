# services/billing-service/src/mappers/billing_plan_mapper.py
"""Mapper for billing plan model to response schemas."""


from ..models import BillingPlan
from ..schemas.billing_plan import BillingPlanIn, BillingPlanPatch, BillingPlanOut
from shared.mappers.crud_mapper import CRUDMapper

class BillingPlanMapper(CRUDMapper[
    BillingPlan, BillingPlanIn, BillingPlanPatch, BillingPlanOut
]):
    model_cls  = BillingPlan
    out_schema = BillingPlanOut