# services/billing-service/src/api/v1/trials.py
def create_trial_router(trial_service: TrialService) -> APIRouter:
    """Create trial management router"""
    
    router = APIRouter(prefix="/api/v1/billing/trial", tags=["Trials"])
    
    @router.get("/{merchant_id}")
    async def get_trial_status(
        request: Request,
        merchant_id: UUID,
        merchant_created_at: datetime = Query(...),
        correlation_id: CorrelationIdDep
    ):
        """Get trial status"""
        
        status = await trial_service.get_trial_status(merchant_id, merchant_created_at)
        
        return success_response(
            data=status.__dict__,
            request_id=request.state.request_id,
            correlation_id=correlation_id
        )
    
    @router.post("/{merchant_id}/extend")
    async def extend_trial(
        request: Request,
        merchant_id: UUID,
        data: TrialExtensionRequest,
        current_trial_end: datetime = Query(...),
        correlation_id: CorrelationIdDep
    ):
        """Extend trial (admin only)"""
        
        try:
            result = await trial_service.extend_trial(
                merchant_id=merchant_id,
                additional_days=data.additional_days,
                reason=data.reason,
                extended_by=data.extended_by,
                current_trial_end=current_trial_end,
                correlation_id=correlation_id
            )
            
            return success_response(
                data=result.__dict__,
                request_id=request.state.request_id,
                correlation_id=correlation_id
            )
            
        except BillingError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return router

