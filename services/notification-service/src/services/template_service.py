from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from shared.utils.logger import ServiceLogger
from ..repositories.template_repository import TemplateRepository
from ..models.entities import NotificationTemplate, NotificationTemplateHistory
from ..schemas.requests import TemplateCreate, TemplateUpdate, TemplateClone
from ..schemas.responses import TemplatePreviewResponse, TemplateValidationResponse
from ..utils.template_engine import TemplateEngine
from ..exceptions import (
    TemplateNotFoundError,
    TemplateRenderError,
    DuplicateTemplateName,
    ValidationError
)

class TemplateService:
    """Template management service"""
    
    def __init__(self, template_engine: TemplateEngine, logger: ServiceLogger):
        self.template_engine = template_engine
        self.logger = logger
    
    async def create_template(
        self,
        data: TemplateCreate,
        session: AsyncSession,
        created_by: Optional[str] = None
    ) -> NotificationTemplate:
        """Create new template"""
        repo = TemplateRepository(session)
        
        # Check if name already exists
        existing = await repo.get_by_name(data.name)
        if existing:
            raise DuplicateTemplateName(
                f"Template with name '{data.name}' already exists",
                template_name=data.name
            )
        
        # Validate template syntax
        validation = await self.validate_template_content(
            data.subject_template,
            data.body_template,
            data.variables
        )
        
        if not validation.is_valid:
            raise TemplateRenderError(
                "Invalid template syntax",
                template_name=data.name,
                render_error="; ".join(str(e) for e in validation.syntax_errors)
            )
        
        # Create template
        template = await repo.create(
            name=data.name,
            type=data.type,
            subject_template=data.subject_template,
            body_template=data.body_template,
            variables=data.dict()['variables'],
            description=data.description,
            is_active=data.is_active,
            created_by=created_by
        )
        
        # Create history entry
        await self._create_history_entry(
            template, "create", created_by, session
        )
        
        await session.commit()
        return template
    
    async def update_template(
        self,
        template_id: UUID,
        data: TemplateUpdate,
        session: AsyncSession,
        updated_by: Optional[str] = None
    ) -> NotificationTemplate:
        """Update existing template"""
        repo = TemplateRepository(session)
        
        template = await repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(
                f"Template {template_id} not found",
                template_name=str(template_id)
            )
        
        # Validate if template content is being updated
        if data.subject_template or data.body_template:
            validation = await self.validate_template_content(
                data.subject_template or template.subject_template,
                data.body_template or template.body_template,
                data.variables or template.variables
            )
            
            if not validation.is_valid:
                raise TemplateRenderError(
                    "Invalid template syntax",
                    template_name=template.name,
                    render_error="; ".join(str(e) for e in validation.syntax_errors)
                )
        
        # Update template
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        # Create history entry
        await self._create_history_entry(
            template, "update", updated_by, session
        )
        
        await session.commit()
        return template
    
    async def delete_template(
        self,
        template_id: UUID,
        session: AsyncSession,
        deleted_by: Optional[str] = None
    ) -> bool:
        """Soft delete template"""
        repo = TemplateRepository(session)
        
        template = await repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(
                f"Template {template_id} not found",
                template_name=str(template_id)
            )
        
        # Soft delete
        template.is_active = False
        
        # Create history entry
        await self._create_history_entry(
            template, "delete", deleted_by, session
        )
        
        await session.commit()
        return True
    
    async def get_template(
        self,
        template_id: UUID,
        session: AsyncSession
    ) -> Optional[NotificationTemplate]:
        """Get template by ID"""
        repo = TemplateRepository(session)
        return await repo.get_by_id(template_id)
    
    async def list_templates(
        self,
        session: AsyncSession,
        type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[NotificationTemplate]:
        """List templates with filters"""
        repo = TemplateRepository(session)
        
        filters = {}
        if type:
            filters['type'] = type
        if is_active is not None:
            filters['is_active'] = is_active
        
        return await repo.find(
            filters=filters,
            order_by=["-created_at"],
            skip=skip,
            limit=limit
        )
    
    async def preview_template(
        self,
        template_id: UUID,
        dynamic_content: Dict[str, Any],
        session: AsyncSession
    ) -> TemplatePreviewResponse:
        """Preview template with sample data"""
        repo = TemplateRepository(session)
        
        template = await repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(
                f"Template {template_id} not found",
                template_name=str(template_id)
            )
        
        # Add global variables
        context = {
            **dynamic_content,
            'unsubscribe_url': 'https://glamyouup.com/unsubscribe?token=PREVIEW_TOKEN'
        }
        
        # Render template
        try:
            subject = self.template_engine.render(template.subject_template, context)
            body_html = self.template_engine.render(template.body_template, context)
            body_text = self.template_engine.html_to_text(body_html)
        except Exception as e:
            raise TemplateRenderError(
                f"Preview failed: {e}",
                template_name=template.name,
                render_error=str(e)
            )
        
        # Check for missing/unused variables
        template_vars = self.template_engine.extract_variables(
            template.subject_template + " " + template.body_template
        )
        
        provided_vars = set(dynamic_content.keys())
        required_vars = set(template.variables.get('required', []))
        
        missing_vars = required_vars - provided_vars
        unused_vars = provided_vars - set(template_vars)
        
        return TemplatePreviewResponse(
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            missing_variables=list(missing_vars),
            unused_variables=list(unused_vars)
        )
    
    async def validate_template(
        self,
        template_id: UUID,
        session: AsyncSession
    ) -> TemplateValidationResponse:
        """Validate template syntax"""
        repo = TemplateRepository(session)
        
        template = await repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(
                f"Template {template_id} not found",
                template_name=str(template_id)
            )
        
        return await self.validate_template_content(
            template.subject_template,
            template.body_template,
            template.variables
        )
    
    async def validate_template_content(
        self,
        subject_template: str,
        body_template: str,
        variables: Dict[str, List[str]]
    ) -> TemplateValidationResponse:
        """Validate template content"""
        # Validate subject
        subject_valid, subject_errors, subject_warnings = self.template_engine.validate_template(
            subject_template
        )
        
        # Validate body
        body_valid, body_errors, body_warnings = self.template_engine.validate_template(
            body_template
        )
        
        # Combine results
        all_errors = subject_errors + body_errors
        all_warnings = subject_warnings + body_warnings
        
        # Check for unused variables
        template_vars = set(self.template_engine.extract_variables(
            subject_template + " " + body_template
        ))
        
        defined_vars = set(variables.get('required', [])) | set(variables.get('optional', []))
        unused_defined = defined_vars - template_vars
        
        if unused_defined:
            all_warnings.extend([
                f"Variable '{var}' is defined but not used in template"
                for var in unused_defined
            ])
        
        return TemplateValidationResponse(
            is_valid=subject_valid and body_valid,
            syntax_errors=all_errors,
            warnings=all_warnings
        )
    
    async def clone_template(
        self,
        template_id: UUID,
        data: TemplateClone,
        session: AsyncSession,
        created_by: Optional[str] = None
    ) -> NotificationTemplate:
        """Clone existing template"""
        repo = TemplateRepository(session)
        
        # Get original template
        original = await repo.get_by_id(template_id)
        if not original:
            raise TemplateNotFoundError(
                f"Template {template_id} not found",
                template_name=str(template_id)
            )
        
        # Check if new name already exists
        existing = await repo.get_by_name(data.name)
        if existing:
            raise DuplicateTemplateName(
                f"Template with name '{data.name}' already exists",
                template_name=data.name
            )
        
        # Create clone
        clone_data = TemplateCreate(
            name=data.name,
            type=original.type,
            subject_template=original.subject_template,
            body_template=original.body_template,
            variables=original.variables,
            description=data.description or f"Clone of {original.name}",
            is_active=True
        )
        
        return await self.create_template(clone_data, session, created_by)
    
    async def _create_history_entry(
        self,
        template: NotificationTemplate,
        change_type: str,
        changed_by: Optional[str],
        session: AsyncSession
    ):
        """Create template history entry"""
        # Get current version
        stmt = select(func.max(NotificationTemplateHistory.version)).where(
            NotificationTemplateHistory.template_id == template.id
        )
        result = await session.execute(stmt)
        current_version = (result.scalar() or 0) + 1
        
        # Create history entry
        history = NotificationTemplateHistory(
            template_id=template.id,
            version=current_version,
            name=template.name,
            type=template.type,
            subject_template=template.subject_template,
            body_template=template.body_template,
            variables=template.variables,
            description=template.description,
            changed_by=changed_by,
            change_type=change_type
        )
        
        session.add(history)