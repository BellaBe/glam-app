from uuid import UUID

from fastapi import APIRouter, Body, Path, status

from shared.api import ApiResponse, success_response
from shared.api.dependencies import ClientAuthDep, PlatformContextDep, RequestContextDep

from ...dependencies import PurchaseServiceDep
from ...schemas.billing import PurchaseCreatedOut, PurchaseCreateIn, PurchaseOut

purchases_router = APIRouter(prefix="/purchases", tags=["Purchases"])


@purchases_router.post(
    "",
    response_model=ApiResponse[PurchaseCreatedOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create credit purchase",
)
async def create_purchase(
    purchase_service: PurchaseServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
    body: PurchaseCreateIn = Body(...),
):
    """Create credit pack purchase"""
    merchant_id = UUID(auth.shop)

    result = await purchase_service.create_purchase(merchant_id=merchant_id, shop_domain=platform.domain, data=body)

    return success_response(data=result, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@purchases_router.get("", response_model=ApiResponse[list[PurchaseOut]], summary="List purchases")
async def list_purchases(
    purchase_service: PurchaseServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    platform: PlatformContextDep,
):
    """List purchases for merchant"""
    merchant_id = UUID(auth.shop)

    purchases = await purchase_service.list_purchases(merchant_id)

    return success_response(data=purchases, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@purchases_router.get("/{purchase_id}", response_model=ApiResponse[PurchaseOut], summary="Get purchase")
async def get_purchase(
    purchase_service: PurchaseServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    purchase_id: UUID = Path(...),
):
    """Get single purchase by ID"""
    result = await purchase_service.get_purchase(purchase_id)

    return success_response(data=result, request_id=ctx.request_id, correlation_id=ctx.correlation_id)
