# services/notification-service/src/templates/template_renderer.py
"""Template renderer with Jinja2 and global variables support"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from jinja2 import Environment, Template, TemplateError, select_autoescape
from markupsafe import Markup
import html2text
import logging

from .email_templates import EmailTemplates


logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Renders email templates with global and dynamic variables"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize template renderer with configuration"""
        self.config = config
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
    
    def get_global_variables(self, unsubscribe_token: str) -> Dict[str, Any]:
        """Get global variables available in all templates"""
        return {
            "support_url": self.config.get("support_url", "https://support.glamyouup.com"),
            "unsubscribe_url": f"{self.config.get('app_url', 'https://app.glamyouup.com')}/unsubscribe/{unsubscribe_token}",
            "current_year": datetime.now().year,
            "platform_name": "GlamYouUp"
        }
    
    def render_template(
        self, 
        notification_type: str, 
        dynamic_content: Dict[str, Any],
        unsubscribe_token: str
    ) -> Tuple[str, str, str]:
        """
        Render template with global and dynamic variables
        
        Returns:
            Tuple of (subject, html_body, text_body)
        """
        try:
            # Get template
            template_data = EmailTemplates.get_template(notification_type)
            
            # Validate required variables
            validation = EmailTemplates.validate_variables(notification_type, dynamic_content)
            if not validation["is_valid"]:
                raise ValueError(f"Missing required variables: {validation['missing_required']}")
            
            # Merge global and dynamic variables
            global_vars = self.get_global_variables(unsubscribe_token)
            all_variables = {**global_vars, **dynamic_content}
            
            # Render subject
            subject_template = self.env.from_string(template_data["subject"])
            subject = subject_template.render(**all_variables)
            
            # Render HTML body
            body_template = self.env.from_string(template_data["body"])
            html_body = body_template.render(**all_variables)
            
            # Generate plain text version
            text_body = self.html2text.handle(html_body)
            
            # Log unused variables as warning
            if validation["unused_variables"]:
                logger.warning(
                    f"Unused variables in {notification_type} template: {validation['unused_variables']}"
                )
            
            return subject, html_body, text_body
            
        except TemplateError as e:
            logger.error(f"Template rendering error for {notification_type}: {e}")
            raise ValueError(f"Failed to render template: {e}")
        except Exception as e:
            logger.error(f"Unexpected error rendering {notification_type}: {e}")
            raise
    
    def preview_template(
        self, 
        notification_type: str, 
        sample_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Preview template with sample data"""
        # Default sample data if none provided
        if sample_data is None:
            sample_data = self._get_default_sample_data(notification_type)
        
        # Use a dummy unsubscribe token for preview
        dummy_token = "preview_token_123456"
        
        try:
            subject, html_body, text_body = self.render_template(
                notification_type, 
                sample_data, 
                dummy_token
            )
            
            validation = EmailTemplates.validate_variables(notification_type, sample_data)
            
            return {
                "subject": subject,
                "body_html": html_body,
                "body_text": text_body,
                "missing_variables": validation["missing_required"],
                "unused_variables": validation["unused_variables"],
                "sample_data_used": sample_data
            }
        except Exception as e:
            return {
                "error": str(e),
                "sample_data_used": sample_data
            }
    
    def _get_default_sample_data(self, notification_type: str) -> Dict[str, Any]:
        """Get default sample data for template preview"""
        defaults = {
            "welcome": {
                "shop_name": "Example Fashion Store"
            },
            "registration_finish": {
                "product_count": 150
            },
            "registration_sync": {
                "added_count": 25,
                "updated_count": 10,
                "removed_count": 5
            },
            "billing_expired": {
                "plan_name": "Monthly Pro Plan",
                "renewal_link": "https://app.glamyouup.com/billing/renew"
            },
            "billing_changed": {
                "plan_name": "Annual Business Plan"
            },
            "billing_low_credits": {
                "current_balance": "125.50",
                "days_remaining": 5,
                "expected_depletion_date": "January 20, 2025",
                "billing_link": "https://app.glamyouup.com/billing"
            },
            "billing_zero_balance": {
                "deactivation_time": "January 16, 2025 at 2:00 AM EST",
                "billing_link": "https://app.glamyouup.com/billing"
            },
            "billing_deactivated": {
                "reason": "zero balance",
                "reactivation_link": "https://app.glamyouup.com/billing/reactivate"
            }
        }
        
        return defaults.get(notification_type, {"content": "Sample notification content"})
    
    def validate_template_syntax(self, subject: str, body: str) -> Dict[str, Any]:
        """Validate Jinja2 template syntax"""
        errors = []
        warnings = []
        
        # Validate subject
        try:
            self.env.from_string(subject)
        except TemplateError as e:
            errors.append(f"Subject template error: {e}")
        
        # Validate body
        try:
            template = self.env.from_string(body)
            
            # Extract variables used in template
            ast = self.env.parse(body)
            undeclared = ast.find_all(self.env.filters['undefined'])
            
        except TemplateError as e:
            errors.append(f"Body template error: {e}")
        
        # Check for common issues
        if "{{" in body and "}}" not in body:
            errors.append("Unclosed variable tag detected")
        if "{%" in body and "%}" not in body:
            errors.append("Unclosed block tag detected")
        
        return {
            "is_valid": len(errors) == 0,
            "syntax_errors": errors,
            "warnings": warnings
        }


# Example usage and configuration
if __name__ == "__main__":
    # Example configuration
    config = {
        "support_url": "https://support.glamyouup.com",
        "app_url": "https://app.glamyouup.com"
    }
    
    # Initialize renderer
    renderer = TemplateRenderer(config)
    
    # Example: Render welcome email
    dynamic_content = {
        "shop_name": "Fashion Boutique",
        "shop_id": "123e4567-e89b-12d3-a456-426614174000",
        "shop_domain": "fashion-boutique.myshopify.com"
    }
    
    subject, html_body, text_body = renderer.render_template(
        "welcome", 
        dynamic_content,
        "unique_unsubscribe_token_123"
    )
    
    print(f"Subject: {subject}")
    print(f"HTML Body Length: {len(html_body)}")
    print(f"Text Body Preview: {text_body[:200]}...")
    
    # Example: Preview template
    preview = renderer.preview_template("billing_low_credits")
    print(f"\nPreview: {preview['subject']}")
    print(f"Missing Variables: {preview['missing_variables']}")
    print(f"Unused Variables: {preview['unused_variables']}")