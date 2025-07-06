# services/notification-service/src/services/template_service.py
"""
Template Service - File-based implementation

Responsibilities:
1. Load templates from EmailTemplates class (file-based)
2. Validate required variables
3. Render templates using Jinja2
4. Generate plain text versions
5. Provide template preview functionality
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import html2text
from jinja2 import Environment, TemplateError, select_autoescape, meta

from shared.utils.logger import ServiceLogger
from ..templates.email_templates import EmailTemplates
from ..exceptions import (
    TemplateNotFoundError,
    TemplateRenderError,
    ValidationError,
)
from ..config import ServiceConfig


class TemplateService:
    """
    Service for managing and rendering file-based email templates.
    All templates are defined in EmailTemplates class.
    """
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        """
        Initialize template service
        
        Args:
            config: Service configuration containing URLs
            logger: Service logger
        """
        self.config = config
        self.logger = logger
        
        # Initialize Jinja2 environment
        self.env = Environment(
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize html2text for plain text conversion
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = True
        self.html2text.body_width = 78
        
        # Cache compiled templates
        self._template_cache: Dict[str, Any] = {}
    
    async def get_template_for_type(self, notification_type: str) -> Optional[Dict[str, Any]]:
        """
        Get template data for a specific notification type
        
        Args:
            notification_type: Type of notification (e.g., 'welcome', 'billing_expired')
            
        Returns:
            Template data or None if not found
        """
        try:
            template_data = EmailTemplates.get_template(notification_type)
            return {
                'type': notification_type,
                'subject': template_data['subject'],
                'body': template_data['body'],
                'variables': template_data['variables']
            }
        except ValueError:
            self.logger.warning(f"Template not found for type: {notification_type}")
            return None
    
    async def render_template(
        self,
        template: Dict[str, Any],
        dynamic_content: Dict[str, Any],
        unsubscribe_token: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        Render email template with provided variables
        
        Args:
            template: Template data from get_template_for_type
            dynamic_content: Variables to inject into template
            unsubscribe_token: Token for unsubscribe URL (optional for non-marketing)
            
        Returns:
            Tuple of (subject, html_body, text_body)
            
        Raises:
            ValidationError: If required variables are missing
            TemplateRenderError: If template rendering fails
        """
        notification_type = template['type']
        
        # Validate required variables
        validation = self._validate_variables(template, dynamic_content)
        if not validation['is_valid']:
            raise ValidationError(
                f"Missing required variables for {notification_type}: {validation['missing_required']}"
            )
        
        # Log unused variables as warning
        if validation['unused_variables']:
            self.logger.warning(
                f"Unused variables in {notification_type} template",
                extra={
                    'notification_type': notification_type,
                    'unused_variables': validation['unused_variables']
                }
            )
        
        # Prepare context with global and dynamic variables
        context = self._prepare_context(dynamic_content, unsubscribe_token)
        
        try:
            # Render subject
            subject_template = self._get_or_compile_template(f"{notification_type}_subject", template['subject'])
            subject = subject_template.render(**context)
            
            # Render HTML body
            body_template = self._get_or_compile_template(f"{notification_type}_body", template['body'])
            html_body = body_template.render(**context)
            
            # Generate plain text version
            text_body = self.html2text.handle(html_body)
            
            self.logger.info(
                f"Successfully rendered {notification_type} template",
                extra={'notification_type': notification_type}
            )
            
            return subject, html_body, text_body
            
        except TemplateError as e:
            self.logger.error(
                f"Template rendering failed for {notification_type}",
                extra={
                    'notification_type': notification_type,
                    'error': str(e)
                }
            )
            raise TemplateRenderError(
                f"Failed to render {notification_type} template: {e}",
                template_name=notification_type,
                render_error=str(e)
            )
    
    def _prepare_context(
        self,
        dynamic_content: Dict[str, Any],
        unsubscribe_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare template context with global and dynamic variables"""
        
        # Global variables available in all templates
        global_vars = {
            'platform_name': 'GlamYouUp',
            'current_year': datetime.now().year,
            'support_url': 'https://support.glamyouup.com', # TODO: Use config value
        }
        
        # Add unsubscribe URL only if token is provided (marketing emails)
        if unsubscribe_token:
            app_url = 'https://app.glamyouup.com' # TODO: Use config value
            global_vars['unsubscribe_url'] = f"{app_url}/unsubscribe/{unsubscribe_token}"
        else:
            # For non-marketing emails, provide empty string to avoid template errors
            global_vars['unsubscribe_url'] = ''
        
        # Merge global and dynamic variables
        return {**global_vars, **dynamic_content}
    
    def _validate_variables(
        self,
        template: Dict[str, Any],
        provided_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that all required variables are provided"""
        
        template_vars = template['variables']
        required = set(template_vars['required'])
        optional = set(template_vars['optional'])
        
        # Global variables that are always available
        global_vars = {'platform_name', 'current_year', 'support_url', 'unsubscribe_url'}
        
        # Variables provided
        provided = set(provided_variables.keys()) | global_vars
        
        # Check for missing required variables
        missing_required = required - provided
        
        # Check for unused variables (excluding globals)
        all_expected = required | optional | global_vars
        unused = set(provided_variables.keys()) - all_expected
        
        return {
            'is_valid': len(missing_required) == 0,
            'missing_required': list(missing_required),
            'unused_variables': list(unused),
            'all_variables': list(all_expected)
        }
    
    def _get_or_compile_template(self, cache_key: str, template_string: str):
        """Get compiled template from cache or compile and cache it"""
        if cache_key not in self._template_cache:
            self._template_cache[cache_key] = self.env.from_string(template_string)
        return self._template_cache[cache_key]
    
    async def preview_template(
        self,
        notification_type: str,
        sample_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Preview template with sample data
        
        Args:
            notification_type: Type of notification to preview
            sample_data: Optional sample data, uses defaults if not provided
            
        Returns:
            Preview data including rendered content and validation info
        """
        # Get template
        template = await self.get_template_for_type(notification_type)
        if not template:
            return {
                'error': f'Template not found for type: {notification_type}',
                'notification_type': notification_type
            }
        
        # Use default sample data if none provided
        if sample_data is None:
            sample_data = self._get_default_sample_data(notification_type)
        
        # Use dummy token for preview
        dummy_token = 'preview_token_123456'
        
        try:
            # Render template
            subject, html_body, text_body = await self.render_template(
                template,
                sample_data,
                dummy_token
            )
            
            # Get validation info
            validation = self._validate_variables(template, sample_data)
            
            return {
                'subject': subject,
                'body_html': html_body,
                'body_text': text_body,
                'missing_variables': validation['missing_required'],
                'unused_variables': validation['unused_variables'],
                'all_variables': validation['all_variables'],
                'sample_data_used': sample_data,
                'notification_type': notification_type
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'notification_type': notification_type,
                'sample_data_used': sample_data
            }
    
    def _get_default_sample_data(self, notification_type: str) -> Dict[str, Any]:
        """Get default sample data for template preview"""
        
        defaults = {
            'welcome': {
                'shop_name': 'Example Fashion Store',
                'shop_domain': 'example-store.myshopify.com'
            },
            'registration_finish': {
                'product_count': 150
            },
            'registration_sync': {
                'added_count': 25,
                'updated_count': 10,
                'removed_count': 5
            },
            'billing_expired': {
                'plan_name': 'Professional Plan',
                'renewal_link': 'https://app.glamyouup.com/billing/renew'
            },
            'billing_changed': {
                'plan_name': 'Enterprise Plan'
            },
            'billing_low_credits': {
                'current_balance': '125.50',
                'days_remaining': 5,
                'expected_depletion_date': 'January 20, 2025',
                'billing_link': 'https://app.glamyouup.com/billing'
            },
            'billing_zero_balance': {
                'deactivation_time': 'January 16, 2025 at 2:00 AM UTC',
                'billing_link': 'https://app.glamyouup.com/billing'
            },
            'billing_deactivated': {
                'reason': 'insufficient credits',
                'reactivation_link': 'https://app.glamyouup.com/billing/reactivate'
            }
        }
        
        return defaults.get(
            notification_type,
            {'content': 'Sample notification content'}
        )
    
    def validate_template_syntax(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Validate Jinja2 template syntax
        
        Args:
            subject: Subject template string
            body: Body template string
            
        Returns:
            Validation results with errors and warnings
        """
        errors = []
        warnings = []
        
        # Validate subject template
        try:
            subject_ast = self.env.parse(subject)
            subject_vars = meta.find_undeclared_variables(subject_ast)
        except TemplateError as e:
            errors.append(f"Subject template error: {str(e)}")
        
        # Validate body template
        try:
            body_ast = self.env.parse(body)
            body_vars = meta.find_undeclared_variables(body_ast)
        except TemplateError as e:
            errors.append(f"Body template error: {str(e)}")
        
        # Check for common issues
        if '{{' in subject + body and not '}}' in subject + body:
            warnings.append("Possible unclosed variable tag detected")
        
        if '{%' in subject + body and not '%}' in subject + body:
            warnings.append("Possible unclosed block tag detected")
        
        return {
            'is_valid': len(errors) == 0,
            'syntax_errors': errors,
            'warnings': warnings
        }
    
    def get_available_types(self) -> List[str]:
        """Get list of all available notification types"""
        return EmailTemplates.get_all_types()
    
    def clear_template_cache(self):
        """Clear the compiled template cache"""
        self._template_cache.clear()
        self.logger.info("Template cache cleared")


# Example usage
"""
# Initialize service
config = {
    'app_url': 'https://app.glamyouup.com',
    'support_url': 'https://support.glamyouup.com'
}
template_service = TemplateService(config, logger)

# Get and render a template
template = await template_service.get_template_for_type('welcome')
if template:
    subject, html, text = await template_service.render_template(
        template,
        {'shop_name': 'My Shop', 'shop_domain': 'myshop.com'},
        unsubscribe_token='abc123'  # Only for marketing emails
    )

# Preview a template
preview = await template_service.preview_template('billing_expired')
print(preview['subject'])
"""