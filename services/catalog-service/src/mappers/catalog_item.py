# src/mappers/item_mapper.py

from shared.mappers.crud_mapper import CRUDMapper
from ..models.catalog_item import CatalogItem
from ..schemas.catalog_item import CatalogItemOut, CatalogItemIn, CatalogItemPatch

class ItemMapper(CRUDMapper[CatalogItem, CatalogItemIn, CatalogItemPatch, CatalogItemOut]):
    """CRUD mapper for Item"""
    model_cls = CatalogItem
    out_schema = CatalogItemOut