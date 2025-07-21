# mappers/generic.py
from __future__ import annotations
from typing import TypeVar, Generic, List
from pydantic import BaseModel, TypeAdapter
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect

ModelT = TypeVar('ModelT', bound=DeclarativeBase)
InT    = TypeVar('InT',    bound=BaseModel)
PatchT = TypeVar('PatchT', bound=BaseModel | None)
OutT   = TypeVar('OutT',   bound=BaseModel)

class CRUDMapper(Generic[ModelT, InT, PatchT, OutT]):
    """Bidirectional bridge between SQLAlchemy models and Pydantic DTOs."""

    model_cls: type[ModelT]
    out_schema: type[OutT]

    # ---------- CREATE ---------- #
    def to_model(self, dto: InT, **extra) -> ModelT:
        return self.model_cls(**dto.model_dump(), **extra)

    # ---------- PATCH ---------- #
    def patch_model(self, obj: ModelT, patch: PatchT) -> None:
        if patch is None:
            return
        for field, value in patch.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        

    # ---------- READ ---------- #
    def to_out(self, obj: ModelT) -> OutT:
        # from_attributes=True must be set on OutT
        return self.out_schema.model_validate(obj)

    def list_to_out(self, objs: List[ModelT]) -> List[OutT]:
        # faster validation for big lists
        ta = TypeAdapter(List[self.out_schema])  # type: ignore[arg-type]
        return ta.validate_python(objs)

    # ---------- HELPER ---------- #
    @staticmethod
    def is_dirty(obj: ModelT) -> bool:
        return bool(inspect(obj).attrs.modified)
