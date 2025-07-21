# services/billing-service/src/repositories/billing_repository.py
from shared.database import Repository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import List

from ..models import BillingPlan
from ..exceptions import BillingPlanNotFoundError


class BillingPlanRepository(Repository[BillingPlan]):
    """Repository for billing plan operations"""
    
    def __init__(self, 
                model_class: type[BillingPlan],
                session_factory: async_sessionmaker[AsyncSession]):
        """Initialize the repository with model class and session factory"""
        super().__init__(model_class, session_factory)
        
    async def create(self, plan_data: BillingPlan) -> BillingPlan | None:
        """Create a new billing plan"""
        async for session in self._session():
            session.add(plan_data)
            await session.commit()
            await session.refresh(plan_data)
            return plan_data
        
    async def patch(self, plan_id: str, patch_data: BillingPlan) -> BillingPlan | None:
        """Patch an existing billing plan"""
        async for session in self._session():
            stmt = select(self.model).where(self.model.id == plan_id)
            result = await session.execute(stmt)
            plan = result.scalar_one_or_none()
            if not plan:
                raise BillingPlanNotFoundError(f"Billing plan {plan_id} not found")
            
            for key, value in patch_data.__dict__.items():
                setattr(plan, key, value)
            
            await session.commit()
            await session.refresh(plan)
            return plan
        
    async def get_all_plans(self) -> List[BillingPlan] | None:
        """Get all billing plans"""
        async for session in self._session():
            stmt = select(self.model).order_by(self.model.sort_order, self.model.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def find_active_plans(self) -> List[BillingPlan]:
        """Find all active plans ordered by sort_order"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.is_active == True
            ).order_by(self.model.sort_order, self.model.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())
        return []
    
    async def find_plan_by_id(self, plan_id: str) -> BillingPlan:
        """Find a billing plan by its ID"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.id == plan_id
            )
            result = await session.execute(stmt)
            plan = result.scalar_one_or_none()
            if plan:
                return plan
        
        # Ensure an exception is raised if no plan is found
        raise BillingPlanNotFoundError(f"Billing plan {plan_id} not found")
