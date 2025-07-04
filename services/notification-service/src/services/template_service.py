# File: services/notification-service/src/services/template_service.py
"""
Template Service

* Thin façade over **TemplateEngine** (render / validation)  
* Pulls templates from **TemplateRepository** (DB-backed) or
  built-in system templates  
* Adds caching + convenience helpers for preview / stats.

The service **no longer instantiates its own Jinja2 environment**;
it receives a fully-configured `TemplateEngine` instance from the
lifecycle.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from uuid import UUID

from cachetools import TTLCache
import html2text
from jinja2 import TemplateError, meta

from shared.utils.logger import ServiceLogger

from ..repositories.template_repository import TemplateRepository
from ..models.entities import NotificationTemplate
from ..templates.email_templates import EmailTemplates
from ..exceptions import (
    TemplateNotFoundError,
    TemplateRenderError,
    ValidationError,
)
from ..utils.template_engine import TemplateEngine


class TemplateService:
    """High-level template manager (caching, validation, preview)."""

    # --------------------------------------------------------------------- #
    # construction                                                          #
    # --------------------------------------------------------------------- #
    def __init__(
        self,
        template_engine: TemplateEngine,
        template_repository: TemplateRepository,
        logger: ServiceLogger,
    ) -> None:
        self.engine = template_engine        # <-- injected
        self.repo   = template_repository
        self.logger = logger

        # 1-hour TTL cache for most-frequent templates
        self._template_cache: TTLCache[str, NotificationTemplate] = TTLCache(
            maxsize=100, ttl=3600
        )

        # html→text helper
        self._html2text = html2text.HTML2Text()
        self._html2text.ignore_links   = False
        self._html2text.ignore_images  = True
        self._html2text.body_width     = 78

        # built-in “system” templates
        self._system_templates = EmailTemplates.TEMPLATES

    # --------------------------------------------------------------------- #
    # public API                                                            #
    # --------------------------------------------------------------------- #
    async def get_template_for_type(                   # <- cache + fallback
        self,
        notification_type: str,
    ) -> Optional[NotificationTemplate]:
        cache_key = f"type:{notification_type}"
        tmpl = self._template_cache.get(cache_key)

        if tmpl and tmpl.is_active:
            return tmpl

        tmpl = await self.repo.get_active_by_type(notification_type)
        if not tmpl:
            tmpl = await self._get_system_template(notification_type)

        if tmpl:
            self._template_cache[cache_key] = tmpl
        return tmpl

    async def render_template(
        self,
        template: NotificationTemplate,
        dynamic_content: Dict[str, Any],
        unsubscribe_token: str,
    ) -> Tuple[str, str, str]:
        """Render → (subject, html_body, text_body)."""
        # validate variables -------------------------------------------------
        validation = self._validate_required_variables(
            template, dynamic_content
        )
        if not validation["is_valid"]:
            raise ValidationError(
                f"Missing required variables: {validation['missing_required']}"
            )

        ctx = self._prepare_context(dynamic_content, unsubscribe_token)

        try:
            subject = self.engine.render(template.subject_template, ctx)
            html    = self.engine.render(template.body_template,    ctx)
            text    = self._html2text.handle(html)

            if validation["unused_variables"]:
                self.logger.warning(
                    "Unused variables in %s template: %s",
                    template.type,
                    validation["unused_variables"],
                    extra={"template_id": str(template.id)},
                )

            return subject, html, text

        except TemplateError as e:
            raise TemplateRenderError(
                f"Template rendering error: {e}",
                template_name=template.name,
                render_error=str(e),
            )

    async def preview_template(
        self,
        notification_type: str,
        sample_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Render a preview with sample data; return diagnostics."""
        tmpl = await self.get_template_for_type(notification_type)
        if not tmpl:
            return {"error": f"No template found for type {notification_type}"}

        sample_data = sample_data or self._get_default_sample_data(
            notification_type
        )

        try:
            subj, html, txt = await self.render_template(
                tmpl, sample_data, unsubscribe_token="preview_token"
            )
            validation = self._validate_required_variables(tmpl, sample_data)
            return {
                "subject": subj,
                "body_html": html,
                "body_text": txt,
                "missing_variables": validation["missing_required"],
                "unused_variables": validation["unused_variables"],
                "sample_data_used": sample_data,
                "template_name": tmpl.name,
                "template_type": tmpl.type,
            }
        except Exception as e:  # noqa: BLE001
            return {"error": str(e), "sample_data_used": sample_data}

    # --------------------------------------------------------------------- #
    # validation helpers                                                    #
    # --------------------------------------------------------------------- #
    def validate_template_syntax(
        self,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """Dry-run compile + simple lint."""
        is_valid, errors, warnings = self.engine.validate_template(subject)
        is_valid2, errors2, warnings2 = self.engine.validate_template(body)
        return {
            "is_valid": is_valid and is_valid2,
            "syntax_errors": errors + errors2,
            "warnings": warnings + warnings2,
        }

    # --------------------------------------------------------------------- #
    # internals                                                             #
    # --------------------------------------------------------------------- #
    def _prepare_context(
        self,
        dynamic_content: Dict[str, Any],
        unsubscribe_token: str,
    ) -> Dict[str, Any]:
        globals_ = {
            "support_url": "https://support.glamyouup.com",
            "unsubscribe_url": f"https://app.glamyouup.com/unsubscribe/{unsubscribe_token}",
            "current_year": datetime.now().year,
            "platform_name": "GlamYouUp",
        }
        return {**globals_, **dynamic_content}

    def _validate_required_variables(
        self,
        template: NotificationTemplate,
        provided: Dict[str, Any],
    ) -> Dict[str, Any]:
        required = set(template.variables.get("required", []))
        optional = set(template.variables.get("optional", []))
        provided_vars = set(provided.keys())

        globals_ = {
            "unsubscribe_url",
            "support_url",
            "current_year",
            "platform_name",
        }
        provided_vars |= globals_

        missing = required - provided_vars
        unused  = (provided_vars - globals_) - (required | optional)

        return {
            "is_valid": not missing,
            "missing_required": list(missing),
            "unused_variables": list(unused),
        }

    async def _get_system_template(
        self,
        notification_type: str,
    ) -> Optional[NotificationTemplate]:
        tmpl_def = self._system_templates.get(notification_type)
        if not tmpl_def:
            return None

        return NotificationTemplate(
            id=UUID(int=0),
            name=f"{notification_type}_system",
            type=notification_type,
            subject_template=tmpl_def["subject"],
            body_template=tmpl_def["body"],
            variables=tmpl_def["variables"],
            is_active=True,
            is_system=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _get_default_sample_data(self, ntype: str) -> Dict[str, Any]:
        # (same dictionary as before, unchanged)
        # … cut for brevity …
        return {
            "content": "Sample notification content",
            "sample_field": "Sample value",
        }

    # cache utils -----------------------------------------------------------
    async def clear_cache(self, notification_type: Optional[str] = None):
        if notification_type:
            self._template_cache.pop(f"type:{notification_type}", None)
        else:
            self._template_cache.clear()
        self.logger.info("Template cache cleared for %s", notification_type or "all")

    async def get_template_by_id(
        self,
        template_id: UUID,
    ) -> Optional[NotificationTemplate]:
        key = f"id:{template_id}"
        tmpl = self._template_cache.get(key)
        if tmpl:
            return tmpl
        tmpl = await self.repo.get_by_id(template_id)
        if tmpl:
            self._template_cache[key] = tmpl
        return tmpl
