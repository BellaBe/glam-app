# services/credit-service/src/mappers/credit_mapper.py
"""Mapper for credit account model to response schemas."""

from typing import List
from uuid import UUID
from shared.mappers import BaseMapper
from ..models.credit import Credit
from ..schemas.credit import CreditResponse, CreateCredit


class CreditMapper(BaseMapper[Credit, CreateCredit, None, CreditResponse]): #type: ignore
    """Maps between credit account model and response schemas"""
    __slots__ = () # Memory optimization
    
    def create_to_model(self, create_schema: CreateCredit, **kwargs) -> Credit:
        return Credit(
            id=UUID(),
            merchant_id=create_schema.merchant_id,
            balance=0,
            last_transaction_id=None,
        )
    
    def model_to_response(self, model: Credit) -> CreditResponse:
        return CreditResponse(
            id = model.id,
            balance=model.balance,
            merchant_id=model.merchant_id,
            last_transaction_id=model.last_transaction_id,
            created_at=model.created_at,
            updated_at=model.updated_at
            
        )
    
    def models_to_responses(self, models: List[Credit]) -> List[CreditResponse]:
        return super().models_to_responses(models)