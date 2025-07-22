# src/api/v1/products.py
from uuid import UUID
from typing import Dict, Any
from fastapi import APIRouter, Path, Query, status, HTTPException
from shared.api import ApiResponse, success_response, RequestContextDep
from ...services.catalog_service import CatalogService
from ...schemas.item import ItemWithAnalysisOut, ProductSearchParams
from ...exceptions import ItemNotFoundError
from ...dependencies import CatalogServiceDep

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

@router.get(
    "/{item_id}",
    response_model=ApiResponse[ItemWithAnalysisOut],
    summary="Get Product",
)
async def get_product(
    svc: CatalogServiceDep,
    ctx: RequestContextDep,
    item_id: UUID = Path(...),
):
    """Get product by ID with analysis results"""
    try:
        out = await svc.get_item(item_id)
        return success_response(out, ctx.request_id, ctx.correlation_id)
    except ItemNotFoundError:
        raise HTTPException(404, "Product not found")

@router.get(
    "",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Search Products",
)
async def search_products(
    svc: CatalogServiceDep,
    ctx: RequestContextDep,
    shop_id: str = Query(...),
    category: str = Query(None),
    status: str = Query(None),
    search: str = Query(None),
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
):
    """Search products with filters and pagination"""
    params = ProductSearchParams(
        shop_id=shop_id,
        category=category,
        status=status,
        search=search,
        limit=limit,
        offset=offset
    )
    
    out = await svc.search_products(params)
    return success_response(out, ctx.request_id, ctx.correlation_id)
