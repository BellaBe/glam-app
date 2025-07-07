# services/scheduler-service/src/mappers/base.py
"""Base mapper for scheduler service"""

from typing import TypeVar, Generic, List, Optional, Type
from abc import ABC, abstractmethod

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
ResponseSchemaType = TypeVar("ResponseSchemaType")


class BaseMapper(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType], ABC):
    """Base mapper for converting between models and schemas"""
    
    @abstractmethod
    def create_to_model(self, create_schema: CreateSchemaType, **kwargs) -> ModelType:
        """Convert create schema to model"""
        pass
    
    @abstractmethod
    def update_to_model(self, model: ModelType, update_schema: UpdateSchemaType) -> ModelType:
        """Apply update schema to model"""
        pass
    
    @abstractmethod
    def model_to_response(self, model: ModelType) -> ResponseSchemaType:
        """Convert model to response schema"""
        pass
    
    def models_to_responses(self, models: List[ModelType]) -> List[ResponseSchemaType]:
        """Convert list of models to response schemas"""
        return [self.model_to_response(model) for model in models]

