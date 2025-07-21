# File: shared/shared/mappers/base.py
from __future__ import annotations

from typing import TypeVar, Generic, List, Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel

# Type variables
ModelT = TypeVar("ModelT")
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)
ResponseT = TypeVar("ResponseT", bound=BaseModel)

class BaseMapper(Generic[ModelT, CreateT, UpdateT, ResponseT], ABC):
    """
    Universal mapper for all entities with optional update support.
    
    Required methods (always implement):
    - create_to_model: Convert create schema to model
    - model_to_response: Convert model to basic response
    
    Optional methods (implement only if your entity needs them):
    - update_to_dict: For updatable entities  
    - model_to_detail_response: For entities with detailed views
    """
    __slots__ = ()  # Memory optimization
    
    @abstractmethod
    def create_to_model(self, create_schema: CreateT, **kwargs) -> ModelT:
        """Convert create schema to model instance."""
        pass
    
    @abstractmethod
    def model_to_response(self, model: ModelT) -> ResponseT:
        """Convert model instance to basic response schema."""
        pass
    
    @abstractmethod
    def models_to_responses(self, models: List[ModelT]) -> List[ResponseT]:
        """Convert list of models to list of response schemas."""
        return [self.model_to_response(model) for model in models]
    
    @abstractmethod
    def update_to_dict(self, update_schema: UpdateT) -> Dict[str, Any]:
        """
        Optional: Convert update schema to dict for partial updates.
        Only implement this method if your entity supports updates.
        """
        return {
            k: v for k, v in update_schema.model_dump(exclude_none=True).items()
        }