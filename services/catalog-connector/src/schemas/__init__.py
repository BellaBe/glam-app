# File: services/connector-service/src/schemas/__init__.py

"""Pydantic schemas for connector service."""

from .catalog import (
    CatalogItem,
    CatalogVariant,
    CatalogImage,
    CatalogItemBatch,
    CatalogDiffBatch,
)
from .commands import (
    FetchItemsCommand,
    FetchItemsDiffCommand,
    ValidateStoreCommand,
)
from .store import (
    StoreConnectionCreate,
    StoreConnectionUpdate,
    StoreConnectionResponse,
)

__all__ = [
    # Catalog schemas
    "CatalogItem",
    "CatalogVariant",
    "CatalogImage",
    "CatalogItemBatch",
    "CatalogDiffBatch",
    
    # Command schemas
    "FetchItemsCommand",
    "FetchItemsDiffCommand",
    "ValidateStoreCommand",
    
    # Store schemas
    "StoreConnectionCreate",
    "StoreConnectionUpdate",
    "StoreConnectionResponse",
]