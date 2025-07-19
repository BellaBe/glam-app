# services/billing-service/src/api/v1/purchases.py
def create_purchase_router(purchase_service: OneTimePurchaseService) -> APIRouter:
    """Create purchase management router"""
    
    router = APIRouter(prefix="/api/v1/billing/purchases", tags=["Purchases"])
    
    @router.post("", response_model=dict)
    async def create_purchase(
        request: Request,
        data: OneTimePurchaseCreateRequest,
        correlation_id: CorrelationIdDep,
        db: DBSessionDep
    ):
        """Create one-time credit purchase"""
        
        try:
            result = await purchase_service.create_purchase(
                merchant_id=data.merchant_id,
                shop_id=data.shop_id,
                credits=data.credits,
                return_url=data.return_url,
                description=data.description,
                correlation_id=correlation_id
            )
            
            return success_response(
                data=result,
                request_id=request.state.request_id,
                correlation_id=correlation_id
            )
            
        except BillingError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return router
