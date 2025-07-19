# services/billing-service/src/api/v1/plans.py
def create_plans_router(plan_repo: BillingPlanRepository) -> APIRouter:
    """Create billing plans router"""
    
    router = APIRouter(prefix="/api/v1/billing/plans", tags=["Plans"])
    
    @router.get("")
    async def list_plans(
        request: Request,
        correlation_id: CorrelationIdDep
    ):
        """List available plans"""
        
        plans = await plan_repo.find_active_plans()
        
        return success_response(
            data=[BillingPlanResponse.from_orm(p).__dict__ for p in plans],
            request_id=request.state.request_id,
            correlation_id=correlation_id
        )
    
    @router.get("/{plan_id}")
    async def get_plan(
        request: Request,
        plan_id: str,
        correlation_id: CorrelationIdDep
    ):
        """Get plan details"""
        
        plan = await plan_repo.find_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return success_response(
            data=BillingPlanResponse.from_orm(plan).__dict__,
            request_id=request.state.request_id,
            correlation_id=correlation_id
        )
    
    return router
