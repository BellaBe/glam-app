# services/notification-service/src/services/template_service.py
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from shared.utils.exceptions import InternalError, NotFoundError
from shared.utils.logger import ServiceLogger


class TemplateService:
    """Service for managing and rendering email templates"""

    def __init__(self, template_path: str, cache_ttl: int = 300, logger: ServiceLogger | None = None):
        self.template_path = Path(template_path)
        self.cache_ttl = cache_ttl  # kept for compatibility; unused without caching
        self.logger = logger

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_path)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["format_currency"] = self._format_currency
        self.env.filters["format_date"] = self._format_date

    @staticmethod
    def _format_currency(value: float) -> str:
        return f"${value:,.2f}"

    @staticmethod
    def _format_date(value: Any) -> str:
        from datetime import datetime

        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if hasattr(value, "strftime"):
            return value.strftime("%B %d, %Y")
        return str(value)

    def get_template_path(self, template_type: str, filename: str) -> Path:
        return self.template_path / template_type / filename

    def template_exists(self, template_type: str) -> bool:
        return (self.template_path / template_type).is_dir()

    def load_subject(self, template_type: str) -> str:
        path = self.get_template_path(template_type, "subject.txt")
        if not path.exists():
            raise NotFoundError(
                f"Subject template not found for {template_type}",
                resource="template",
                resource_id=f"{template_type}/subject.txt",
            )
        return path.read_text(encoding="utf-8").strip()

    def render_template(self, template_type: str, fmt: str, context: dict[str, Any]) -> str:
        """
        Render a template with context

        Args:
            template_type: Template type (e.g., 'welcome')
            fmt: 'html' or 'text'
            context: Template variables
        """
        template_file = "body.html.j2" if fmt == "html" else "body.text.j2"
        template_path = f"{template_type}/{template_file}"

        try:
            template = self.env.get_template(template_path)
            if fmt == "html":
                context = {**context}  # avoid mutating caller's dict
                context["header"] = self._render_shared("header.html.j2", context)
                context["footer"] = self._render_shared("footer.html.j2", context)
            return template.render(**context)

        except TemplateNotFound as e:
            raise NotFoundError(
                f"Template not found: {template_path}",
                resource="template",
                resource_id=template_path,
            ) from e
        except Exception as e:
            raise InternalError(f"Template rendering failed: {e!s}", error_id=template_type) from e

    def _render_shared(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(f"shared/{template_name}")
            return template.render(**context)
        except TemplateNotFound:
            if self.logger:
                self.logger.warning(f"Shared template not found: {template_name}")
            return ""

    def render_email(self, template_type: str, context: dict[str, Any]) -> tuple[str, str, str]:
        if not self.template_exists(template_type):
            raise NotFoundError(
                f"Template type not found: {template_type}",
                resource="template",
                resource_id=template_type,
            )

        subject = self.load_subject(template_type)
        html_body = self.render_template(template_type, "html", context)
        text_body = self.render_template(template_type, "text", context)
        return subject, html_body, text_body
