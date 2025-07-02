from jinja2 import Environment, BaseLoader, TemplateSyntaxError, UndefinedError
from typing import Dict, Any, Tuple, List
import html2text
import re

class SafeTemplateLoader(BaseLoader):
    """Safe template loader that prevents file access"""
    def get_source(self, environment, template):
        raise TemplateError("File access not allowed")

class TemplateEngine:
    """Jinja2 template engine wrapper"""
    
    def __init__(self):
        self.env = Environment(
            loader=SafeTemplateLoader(),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add global variables
        self.env.globals.update({
            'platform_name': 'GlamYouUp',
            'support_url': 'https://glamyouup.com/support',
            'current_year': lambda: datetime.now().year
        })
    
    def render(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render template with context"""
        try:
            template = self.env.from_string(template_str)
            return template.render(**context)
        except UndefinedError as e:
            raise TemplateError(f"Undefined variable: {e}")
        except TemplateSyntaxError as e:
            raise TemplateError(f"Template syntax error: {e}")
    
    def validate_template(self, template_str: str) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
        """Validate template syntax"""
        errors = []
        warnings = []
        
        try:
            # Parse template
            ast = self.env.parse(template_str)
            
            # Check for syntax errors
            self.env.from_string(template_str)
            
            # Extract variables
            from jinja2 import meta
            variables = meta.find_undeclared_variables(ast)
            
            # Check for common issues
            if '{{' in template_str and '}}' not in template_str:
                errors.append({
                    "line": self._find_line_number(template_str, '{{'),
                    "error": "Unclosed variable tag"
                })
            
            if '{%' in template_str and '%}' not in template_str:
                errors.append({
                    "line": self._find_line_number(template_str, '{%'),
                    "error": "Unclosed block tag"
                })
            
            return len(errors) == 0, errors, warnings
            
        except TemplateSyntaxError as e:
            errors.append({
                "line": e.lineno,
                "error": str(e)
            })
            return False, errors, warnings
    
    def extract_variables(self, template_str: str) -> List[str]:
        """Extract all variables from template"""
        try:
            ast = self.env.parse(template_str)
            from jinja2 import meta
            return list(meta.find_undeclared_variables(ast))
        except:
            return []
    
    def html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        return h.handle(html_content).strip()
    
    def _find_line_number(self, content: str, search_str: str) -> int:
        """Find line number of string in content"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_str in line:
                return i
        return 1

class TemplateError(Exception):
    """Template rendering error"""
    pass