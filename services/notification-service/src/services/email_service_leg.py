# services/notification-service/src/services/email_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from botocore.exceptions import ClientError
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Environment, Template, TemplateError

from shared.utils.logger import ServiceLogger
from src.config import Settings
from src.models.api import EmailDeliveryResult

logger = ServiceLogger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers"""
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Send an email"""
        pass


class SMTPProvider(EmailProvider):
    """SMTP email provider"""
    
    def __init__(self, settings: Settings):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.use_tls = settings.smtp_use_tls
        self.from_email = settings.email_from_address
        self.from_name = settings.email_from_name
        
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name or self.from_name} <{from_email or self.from_email}>"
            msg['To'] = to_email
            
            # Add text part
            if body_text:
                text_part = MIMEText(body_text, 'plain')
                msg.attach(text_part)
                
            # Add HTML part
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                use_tls=self.use_tls,
            ) as smtp:
                await smtp.login(self.username, self.password)
                response = await smtp.send_message(msg)
                
            # Extract message ID from response
            message_id = response.get(to_email, "")
            
            return EmailDeliveryResult(
                success=True,
                message_id=message_id,
                details={"provider": "smtp", "response": str(response)}
            )
            
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return EmailDeliveryResult(
                success=False,
                error=str(e),
                details={"provider": "smtp", "error_type": type(e).__name__}
            )


class SendGridProvider(EmailProvider):
    """SendGrid email provider"""
    
    def __init__(self, settings: Settings):
        self.api_key = settings.sendgrid_api_key
        self.from_email = settings.email_from_address
        self.from_name = settings.email_from_name
        self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
        
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Send email via SendGrid"""
        try:
            from_addr = Email(from_email or self.from_email, from_name or self.from_name)
            to_addr = To(to_email)
            
            # Create content
            content = Content("text/html", body_html)
            
            # Create mail
            mail = Mail(from_addr, to_addr, subject, content)
            
            # Add text version if provided
            if body_text:
                mail.add_content(Content("text/plain", body_text))
                
            # Send
            response = self.sg.send(mail)
            
            # Extract message ID from headers
            message_id = response.headers.get('X-Message-Id', '')
            
            return EmailDeliveryResult(
                success=True,
                message_id=message_id,
                details={
                    "provider": "sendgrid",
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
            )
            
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return EmailDeliveryResult(
                success=False,
                error=str(e),
                details={"provider": "sendgrid", "error_type": type(e).__name__}
            )


class SESProvider(EmailProvider):
    """AWS SES email provider"""
    
    def __init__(self, settings: Settings):
        self.from_email = settings.email_from_address
        self.from_name = settings.email_from_name
        self.client = boto3.client(
            'ses',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Send email via AWS SES"""
        try:
            # Prepare message
            message = {
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': body_html}}
            }
            
            if body_text:
                message['Body']['Text'] = {'Data': body_text}
                
            # Prepare source
            source = from_email or self.from_email
            if from_name or self.from_name:
                source = f"{from_name or self.from_name} <{source}>"
                
            # Send email
            response = self.client.send_email(
                Source=source,
                Destination={'ToAddresses': [to_email]},
                Message=message
            )
            
            message_id = response['MessageId']
            
            return EmailDeliveryResult(
                success=True,
                message_id=message_id,
                details={
                    "provider": "ses",
                    "response_metadata": response.get('ResponseMetadata', {})
                }
            )
            
        except ClientError as e:
            logger.error(f"SES send failed: {e}")
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            return EmailDeliveryResult(
                success=False,
                error=f"{error_code}: {error_message}",
                details={
                    "provider": "ses",
                    "error_code": error_code,
                    "error_type": "ClientError"
                }
            )
        except Exception as e:
            logger.error(f"SES send failed: {e}")
            return EmailDeliveryResult(
                success=False,
                error=str(e),
                details={"provider": "ses", "error_type": type(e).__name__}
            )


class EmailService:
    """Main email service that handles template rendering and provider selection"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.jinja_env = Environment(autoescape=True)
        
        # Initialize the appropriate provider
        if settings.email_provider == "smtp":
            self.provider = SMTPProvider(settings)
        elif settings.email_provider == "sendgrid":
            self.provider = SendGridProvider(settings)
        elif settings.email_provider == "ses":
            self.provider = SESProvider(settings)
        else:
            raise ValueError(f"Unknown email provider: {settings.email_provider}")
            
    def render_template(
        self,
        template_str: str,
        variables: Dict[str, Any]
    ) -> str:
        """Render a template with variables"""
        try:
            template = self.jinja_env.from_string(template_str)
            return template.render(**variables)
        except TemplateError as e:
            logger.error(f"Template rendering failed: {e}")
            raise
            
    def extract_text_from_html(self, html: str) -> str:
        """Extract plain text from HTML (simple version)"""
        # This is a very basic implementation
        # In production, use a proper HTML to text converter like html2text
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        # Replace multiple whitespaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Send an email using the configured provider"""
        # If no text version provided, extract from HTML
        if not body_text:
            body_text = self.extract_text_from_html(body_html)
            
        # Add unsubscribe footer if not already present
        if "unsubscribe" not in body_html.lower():
            body_html += """
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; font-size: 12px; color: #666;">
                <p>You're receiving this email because you're subscribed to notifications from GlamYouUp.</p>
                <p><a href="{unsubscribe_link}" style="color: #666;">Unsubscribe from these emails</a></p>
            </div>
            """
            
        logger.info(f"Sending email to {to_email} with subject: {subject}")
        
        result = await self.provider.send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            from_email=from_email,
            from_name=from_name,
        )
        
        if result.success:
            logger.info(f"Email sent successfully to {to_email}, message_id: {result.message_id}")
        else:
            logger.error(f"Failed to send email to {to_email}: {result.error}")
            
        return result
        
    async def send_templated_email(
        self,
        to_email: str,
        subject_template: str,
        body_template: str,
        variables: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Send an email using templates"""
        try:
            # Render subject and body
            subject = self.render_template(subject_template, variables)
            body_html = self.render_template(body_template, variables)
            
            # Send email
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                from_email=from_email,
                from_name=from_name,
            )
        except Exception as e:
            logger.error(f"Failed to send templated email: {e}")
            return EmailDeliveryResult(
                success=False,
                error=str(e),
                details={"error_type": type(e).__name__}
            )