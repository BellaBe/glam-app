# glam-app/shared/database/repository.py
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from .base import Base

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    """
    Generic repository providing basic CRUD operations.
    Services can extend this for specific domain needs.
    """
    
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get(self, id: Any) -> Optional[T]:
        """Get a single record by ID"""
        if not hasattr(self.model, "id"):
            raise AttributeError(f"Model {self.model.__name__} does not have an 'id' attribute.")
        result = await self.session.execute(
            select(self.model).where(getattr(self.model, "id") == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by(self, **kwargs) -> Optional[T]:
        """Get a single record by arbitrary fields"""
        query = select(self.model)
        for key, value in kwargs.items():
            query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_many(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[T]:
        """Get multiple records with optional filtering and pagination"""
        query = select(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
        load_options: Optional[List[Any]] = None
    ) -> List[T]:
        """
        Advanced query method with filtering, sorting, and eager loading.
        
        Args:
            filters: Dictionary of field:value pairs for filtering
            order_by: List of field names to sort by (prefix with - for DESC)
            skip: Number of records to skip
            limit: Maximum number of records to return
            load_options: SQLAlchemy load options (selectinload, joinedload, etc.)
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(
                            getattr(self.model, key).in_(value)
                        )
                    elif value is None:
                        filter_conditions.append(
                            getattr(self.model, key).is_(None)
                        )
                    else:
                        filter_conditions.append(
                            getattr(self.model, key) == value
                        )
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Apply sorting
        if order_by:
            for field in order_by:
                if field.startswith('-'):
                    query = query.order_by(
                        getattr(self.model, field[1:]).desc()
                    )
                else:
                    query = query.order_by(
                        getattr(self.model, field).asc()
                    )
        
        # Apply eager loading
        if load_options:
            for option in load_options:
                query = query.options(option)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, **filters) -> int:
        """Count records with optional filtering"""
        query = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def exists(self, **filters) -> bool:
        """Check if a record exists"""
        count = await self.count(**filters)
        return count > 0
    
    async def create(self, **data) -> T:
        """Create a new record"""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records"""
        instances = [self.model(**data) for data in data_list]
        self.session.add_all(instances)
        await self.session.flush()
        return instances
    
    async def update(self, id: Any, **data) -> Optional[T]:
        """Update a record by ID"""
        instance = await self.get(id)
        if instance:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.session.flush()
        return instance
    
    async def update_many(self, filters: Dict[str, Any], **data) -> int:
        """Update multiple records matching filters"""
        query = update(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        query = query.values(**data)
        result = await self.session.execute(query)
        return result.rowcount
    
    async def delete(self, id: Any) -> bool:
        """Delete a record by ID"""
        instance = await self.get(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
    
    async def delete_many(self, **filters) -> int:
        """Delete multiple records matching filters"""
        query = delete(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.rowcount
    
    async def soft_delete(self, id: Any) -> Optional[T]:
        """Soft delete a record (requires SoftDeleteMixin)"""
        from datetime import datetime, timezone
        
        return await self.update(
            id,
            is_deleted=True,
            deleted_at=datetime.now(timezone.utc)
        )


class SoftDeleteRepository(Repository[T]):
    """Repository that filters out soft-deleted records by default"""
    
    async def get(self, id: Any, include_deleted: bool = False) -> Optional[T]:
        """Get a single record by ID, optionally including soft-deleted"""
        query = select(self.model).where(getattr(self.model, "id") == id)
        
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            query = query.where(getattr(self.model, 'is_deleted') == False)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_many(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        **filters
    ) -> List[T]:
        """Get multiple records, optionally including soft-deleted"""
        query = select(self.model)
        
        # Filter out soft-deleted unless requested
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            query = query.where(getattr(self.model, 'is_deleted') == False)
        
        # Apply other filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def restore(self, id: Any) -> Optional[T]:
        """Restore a soft-deleted record"""
        return await self.update(
            id,
            is_deleted=False,
            deleted_at=None
        )