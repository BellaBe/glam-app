# services/billing-service/src/mappers/one_time_purchase_mapper.py
"""Mapper for one-time purchase model to response schemas."""

from ..models import OneTimePurchase
from ..schemas.one_time_purchase import (
    OneTimePurchaseIn,
    OneTimePurchasePatch,
    OneTimePurchaseOut,
)
from shared.mappers.crud_mapper import CRUDMapper

class OneTimePurchaseMapper(
    CRUDMapper[OneTimePurchase, OneTimePurchaseIn, OneTimePurchasePatch, OneTimePurchaseOut]
):
    model_cls  = OneTimePurchase
    out_schema = OneTimePurchaseOut