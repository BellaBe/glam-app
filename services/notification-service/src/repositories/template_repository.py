from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import Repository
from ..models.entities import NotificationTemplate, NotificationTemplateHistory

class TemplateRepository:
    """Repository for template operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = NotificationTemplate
    
    async def create(self, **kwargs) -> NotificationTemplate:
        """Create new template"""
        template = self.model(**kwargs)
        self.session.add(template)
        await self.session.flush()
        return template
    
    async def get_by_id(self, template_id: UUID) -> Optional[NotificationTemplate]:
        """Get template by ID"""
        stmt = select(self.model).where(self.model.id == template_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[NotificationTemplate]:
        """Get template by name"""
        stmt = select(self.model).where(self.model.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_type_and_name(self, type: str, name: str) -> Optional[NotificationTemplate]:
        """Get template by type and name"""
        stmt = select(self.model).where(
            and_(
                self.model.type == type,
                self.model.name == name
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find(
        self,
        filters: dict = None,
        order_by: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NotificationTemplate]:
        """Find templates with filters"""
        stmt = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        if order_by:
            for order in order_by:
                if order.startswith('-'):
                    stmt = stmt.order_by(getattr(self.model, order[1:]).desc())
                else:
                    stmt = stmt.order_by(getattr(self.model, order))
        
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def count(self, filters: dict = None) -> int:
        """Count templates"""
        stmt = select(func.count(self.model.id))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def get_active_by_type(self, type: str) -> List[NotificationTemplate]:
        """Get all active templates of a type"""
        stmt = select(self.model).where(
            and_(
                self.model.type == type,
                self.model.is_active == True
            )
        ).order_by(self.model.name)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_history(self, template_id: UUID) -> List[NotificationTemplateHistory]:
        """Get template history"""
        stmt = select(NotificationTemplateHistory).where(
            NotificationTemplateHistory.template_id == template_id
        ).order_by(NotificationTemplateHistory.version.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()