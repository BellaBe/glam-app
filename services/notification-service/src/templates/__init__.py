# services/notification-service/src/templates/email_templates.py
"""Email templates for different notification types"""

from typing import Dict, Any
from datetime import datetime


class EmailTemplates:
    """Email template definitions with all required variables"""

    # Base footer template used in all emails
    FOOTER_TEMPLATE = """
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
        <div style="text-align: center; font-size: 12px; color: #666;">
            <p>
                <a href="{{ support_url }}" style="color: #666; text-decoration: none;">Contact Support</a> | 
                <a href="{{ unsubscribe_url }}" style="color: #666; text-decoration: none;">Unsubscribe</a>
            </p>
            <p>&copy; {{ current_year }} {{ platform_name }}. All rights reserved.</p>
        </div>
    </div>
    """

    WELCOME = {
        "subject": "Welcome to GlamYouUp! 🎉",
        "body": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                <h1 style="color: #333;">Welcome to GlamYouUp!</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Hi {{ shop_name }},</p>
                
                <p>Thank you for launching GlamYouUp on your store! We're excited to help you provide an amazing shopping experience for your customers.</p>
                
                <h2 style="color: #666;">Key Features Now Available:</h2>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #333;">✨ Personal Style Analysis</h3>
                    <p>Help customers discover their unique style profile with AI-powered analysis.</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #333;">👗 Best Style Fit Recommendation</h3>
                    <p>Match customers with products that perfectly suit their style preferences.</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #333;">🤳 Proactive Tryon Analysis</h3>
                    <p>Let customers virtually try on products before making a purchase.</p>
                </div>
                
                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin: 30px 0;">
                    <h3 style="color: #1976d2;">Next Steps:</h3>
                    <ol style="color: #555;">
                        <li>Complete product registration to enable AI features</li>
                        <li>Customize your style preferences</li>
                        <li>Start promoting virtual try-on to your customers</li>
                    </ol>
                </div>
                
                <p>If you have any questions, don't hesitate to reach out to our support team!</p>
                
                <p>Best regards,<br>The GlamYouUp Team</p>
                
                """
        + FOOTER_TEMPLATE
        + """
            </div>
        </body>
        </html>
        """,
        "variables": {"required": ["shop_name"], "optional": []},
    }

    REGISTRATION_FINISH = {
        "subject": "Product Registration Complete! ✅",
        "body": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #4caf50; padding: 20px; text-align: center;">
                <h1 style="color: white;">Registration Complete!</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Great news!</p>
                
                <p>We've successfully registered <strong>{{ product_count }}</strong> products from your store with our AI system.</p>
                
                <div style="background-color: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2e7d32;">What This Means:</h3>
                    <ul style="color: #555;">
                        <li>Your products are now ready for AI-powered style analysis</li>
                        <li>Customers can use virtual try-on features</li>
                        <li>Personalized recommendations are active</li>
                    </ul>
                </div>
                
                <p>Your customers can now enjoy the full GlamYouUp experience!</p>
                
                <p>Best regards,<br>The GlamYouUp Team</p>
                
                """
        + FOOTER_TEMPLATE
        + """
            </div>
        </body>
        </html>
        """,
        "variables": {"required": ["product_count"], "optional": []},
    }

    REGISTRATION_SYNC = {
        "subject": "Product Catalog Updated 🔄",
        "body": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #2196f3; padding: 20px; text-align: center;">
                <h1 style="color: white;">Catalog Sync Complete</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Hi there,</p>
                
                <p>We've detected changes in your product catalog and automatically synced them with GlamYouUp.</p>
                
                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1976d2;">Sync Summary:</h3>
                    <ul style="color: #555;">
                        <li><strong>{{ added_count }}</strong> new products added</li>
                        <li><strong>{{ updated_count }}</strong> products updated</li>
                        {% if removed_count > 0 %}
                        <li><strong>{{ removed_count }}</strong> products removed</li>
                        {% endif %}
                    </ul>
                </div>
                
                <p>The updated products are being processed by our AI system and will be ready for virtual try-on shortly.</p>
                
                <p>Best regards,<br>The GlamYouUp Team</p>
                
                """
        + FOOTER_TEMPLATE
        + """
            </div>
        </body>
        </html>
        """,
        "variables": {
            "required": ["added_count", "updated_count"],
            "optional": ["removed_count"],
        },
    }

    BILLING_EXPIRED = {
        "subject": "Your GlamYouUp Subscription Has Expired ⚠️",
        "body": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #ff9800; padding: 20px; text-align: center;">
                <h1 style="color: white;">Subscription Expired</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Hi there,</p>
                
                <p>Your GlamYouUp subscription ({{ plan_name }}) has expired.</p>
                
                <div style="background-color: #fff3e0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #e65100;">What This Means:</h3>
                    <ul style="color: #555;">
                        <li>Virtual try-on features are temporarily disabled</li>
                        <li>AI style recommendations are paused</li>
                        <li>Your product data is safely stored</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ renewal_link }}" style="background-color: #4caf50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Renew Subscription
                    </a>
                </div>
                
                <p>Renew your subscription to continue providing amazing experiences for your customers!</p>
                
                <p>Best regards,<br>The GlamYouUp Team</p>
                
                """
        + FOOTER_TEMPLATE
        + """
            </div>
        </body>
        </html>
        """,
        "variables": {"required": ["plan_name", "renewal_link"], "optional": []},
    }

    BILLING_CHANGED = {
        "subject": "Billing Plan Updated Successfully ✅",
        "body": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #4caf50; padding: 20px; text-align: center;">
                <h1 style="color: white;">Plan Updated!</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Hi there,</p>
                
                <p>Your billing plan has been successfully updated to: <strong>{{ plan_name }}</strong></p>
                
                <div style="background-color: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p>All GlamYouUp features are now active and ready to use!</p>
                </div>
                
                <p>Thank you for continuing to trust GlamYouUp for your virtual try-on needs.</p>
                
                <p>Best regards,<br>The GlamYouUp Team</p>
                
                """
        + FOOTER_TEMPLATE
        + """
            </div>
        </body>
        </html>
        """,
        "variables": {"required": ["plan_name"], "optional": []},
    }

    BILLING_LOW_CREDITS = {
        "subject": "Credit Balance Running Low ⚠️",
        "body": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #ff9800; padding: 20px; text-align: center;">
                <h1 style="color: white;">Low Credit Balance</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Hi there,</p>
                
                <p>Your GlamYouUp credit balance is running low.</p>
                
                <div style="background-color: #fff3e0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #e65100;">Current Status:</h3>
                    <ul style="color: #555;">
                        <li>Current balance: <strong>${{ current_balance }}</strong></li>
                        <li>Estimated days remaining: <strong>{{ days_remaining }} days</strong></li>
                        <li>Expected depletion: <strong>{{ expected_depletion_date }}</strong></li>
                    </ul>
                </div>
                
                <p>To avoid service interruption, please add credits or upgrade your plan.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ billing_link }}" style="background-color: #2196f3; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Add Credits
                    </a>
                </div>
                
                <p>Best regards,<br>The GlamYouUp Team</p>
                
                """
        + FOOTER_TEMPLATE
        + """
            </div>
        </body>
        </html>
        """,
        "variables": {
            "required": [
                "current_balance",
                "days_remaining",
                "expected_depletion_date",
                "billing_link",
            ],
            "optional": [],
        },
    }

    BILLING_ZERO_BALANCE = {
        "subject": "URGENT: Zero Balance - Service Deactivation in 16 Hours 🚨",
        "body": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f44336; padding: 20px; text-align: center;">
                <h1 style="color: white;">Zero Balance Alert</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Hi there,</p>
                
                <p><strong>Your GlamYouUp credit balance has reached $0.</strong></p>
                
                <div style="background-color: #ffebee; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #f44336;">
                    <h3 style="color: #c62828;">⏰ IMPORTANT:</h3>
                    <p style="color: #555; font-size: 16px;">
                        GlamYouUp features will be automatically deactivated at:<br>
                        <strong style="font-size: 18px;">{{ deactivation_time }}</strong>
                    </p>
                </div>
                
                <p>To continue using GlamYouUp without interruption, please add credits immediately.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ billing_link }}" style="background-color: #f44336; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; display: inline-block; font-size: 18px;">
                        Add Credits Now
                    </a>
                </div>
                
                <p>Don't let your customers miss out on the virtual try-on experience!</p>
                
                <p>Best regards,<br>The GlamYouUp Team</p>
                
                """
        + FOOTER_TEMPLATE
        + """
            </div>
        </body>
        </html>
        """,
        "variables": {
            "required": ["deactivation_time", "billing_link"],
            "optional": [],
        },
    }

    BILLING_DEACTIVATED = {
        "subject": "GlamYouUp Features Deactivated 🔒",
        "body": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #757575; padding: 20px; text-align: center;">
                <h1 style="color: white;">Features Deactivated</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Hi there,</p>
                
                <p>GlamYouUp features have been deactivated for your store due to: <strong>{{ reason }}</strong></p>
                
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #424242;">Currently Disabled:</h3>
                    <ul style="color: #555;">
                        <li>Virtual try-on functionality</li>
                        <li>AI style recommendations</li>
                        <li>Product analysis features</li>
                    </ul>
                </div>
                
                <p>Your product data and settings are safely stored and will be restored once you reactivate your account.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ reactivation_link }}" style="background-color: #4caf50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reactivate Account
                    </a>
                </div>
                
                <p>We'd love to have you back!</p>
                
                <p>Best regards,<br>The GlamYouUp Team</p>
                
                """
        + FOOTER_TEMPLATE
        + """
            </div>
        </body>
        </html>
        """,
        "variables": {"required": ["reason", "reactivation_link"], "optional": []},
    }

    @classmethod
    def get_template(cls, notification_type: str) -> Dict[str, Any]:
        """Get template for notification type"""
        templates = {
            "welcome": cls.WELCOME,
            "registration_finish": cls.REGISTRATION_FINISH,
            "registration_sync": cls.REGISTRATION_SYNC,
            "billing_expired": cls.BILLING_EXPIRED,
            "billing_changed": cls.BILLING_CHANGED,
            "billing_low_credits": cls.BILLING_LOW_CREDITS,
            "billing_zero_balance": cls.BILLING_ZERO_BALANCE,
            "billing_deactivated": cls.BILLING_DEACTIVATED,
        }

        return templates.get(
            notification_type,
            {
                "subject": "GlamYouUp Notification",
                "body": "<html><body><p>{{ content }}</p></body></html>",
                "variables": {"required": ["content"], "optional": []},
            },
        )

    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available templates"""
        return {
            "welcome": cls.WELCOME,
            "registration_finish": cls.REGISTRATION_FINISH,
            "registration_sync": cls.REGISTRATION_SYNC,
            "billing_expired": cls.BILLING_EXPIRED,
            "billing_changed": cls.BILLING_CHANGED,
            "billing_low_credits": cls.BILLING_LOW_CREDITS,
            "billing_zero_balance": cls.BILLING_ZERO_BALANCE,
            "billing_deactivated": cls.BILLING_DEACTIVATED,
        }

    @classmethod
    def get_template_info(cls, notification_type: str) -> Dict[str, Any]:
        """Get template information including variables"""
        template = cls.get_template(notification_type)
        return {
            "type": notification_type,
            "subject": template.get("subject", ""),
            "variables": template.get("variables", {"required": [], "optional": []}),
            "has_body": bool(template.get("body")),
        }

    @classmethod
    def validate_variables(
        cls, notification_type: str, provided_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that all required variables are provided"""
        template = cls.get_template(notification_type)
        required_vars = template.get("variables", {}).get("required", [])
        optional_vars = template.get("variables", {}).get("optional", [])

        missing_required = [
            var for var in required_vars if var not in provided_variables
        ]
        unused_variables = [
            var
            for var in provided_variables
            if var
            not in required_vars
            + optional_vars
            + ["unsubscribe_token", "merchant_id", "shop_domain"]
        ]

        return {
            "is_valid": len(missing_required) == 0,
            "missing_required": missing_required,
            "unused_variables": unused_variables,
        }
