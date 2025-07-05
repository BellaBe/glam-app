# -------------------------------
# services/notification-service/src/mappers/base.py
# -------------------------------

"""Base mapper class with common functionality."""

from typing import TypeVar, Generic, Type, List
from abc import ABC, abstractmethod

SchemaT = TypeVar("SchemaT")
ModelT = TypeVar("ModelT")
CreateT = TypeVar("CreateT")
UpdateT = TypeVar("UpdateT")
ResponseT = TypeVar("ResponseT")


class BaseMapper(Generic[ModelT, CreateT, UpdateT, ResponseT], ABC):
    """
    Base mapper for converting between schemas and models.
    
    Provides a consistent interface for all mappers.
    """
    
    @abstractmethod
    def create_to_model(self, create_schema: CreateT, **kwargs) -> ModelT:
        """Convert create schema to model instance."""
        pass
    
    @abstractmethod
    def model_to_response(self, model: ModelT) -> ResponseT:
        """Convert model instance to response schema."""
        pass
    
    def update_to_dict(self, update_schema: UpdateT) -> dict:
        """
        Convert update schema to dictionary for partial updates.
        
        Excludes None values to avoid overwriting with nulls.
        """
        return {
            k: v for k, v in update_schema.model_dump().items() # type: ignore
            if v is not None
        }
    
    def models_to_responses(self, models: List[ModelT]) -> List[ResponseT]:
        """Convert list of models to list of response schemas."""
        return [self.model_to_response(model) for model in models]
