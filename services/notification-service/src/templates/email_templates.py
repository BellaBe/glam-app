# services/notification-service/src/templates/email_templates.py
"""System email templates for all notification types"""

from typing import Dict, Any


class EmailTemplates:
    """System email templates with proper styling and variables"""

    # Base HTML template wrapper for consistent styling
    BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background-color: #6B46C1;
            color: #ffffff;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .content {
            padding: 40px 30px;
        }
        .content h2 {
            color: #6B46C1;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 24px;
        }
        .button {
            display: inline-block;
            padding: 12px 30px;
            background-color: #6B46C1;
            color: #ffffff;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
            margin: 20px 0;
        }
        .button:hover {
            background-color: #553C9A;
        }
        .warning {
            background-color: #FEF3C7;
            border-left: 4px solid #F59E0B;
            padding: 15px;
            margin: 20px 0;
        }
        .error {
            background-color: #FEE2E2;
            border-left: 4px solid #EF4444;
            padding: 15px;
            margin: 20px 0;
        }
        .success {
            background-color: #D1FAE5;
            border-left: 4px solid #10B981;
            padding: 15px;
            margin: 20px 0;
        }
        .metric {
            background-color: #F3F4F6;
            padding: 20px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #6B46C1;
            margin: 5px 0;
        }
        .metric-label {
            color: #6B7280;
            font-size: 14px;
        }
        .footer {
            background-color: #F9FAFB;
            padding: 30px;
            text-align: center;
            font-size: 14px;
            color: #6B7280;
        }
        .footer a {
            color: #6B46C1;
            text-decoration: none;
        }
        .unsubscribe {
            margin-top: 20px;
            font-size: 12px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #E5E7EB;
        }
        th {
            background-color: #F9FAFB;
            font-weight: 600;
            color: #374151;
        }
        .list-item {
            padding: 10px 0;
            border-bottom: 1px solid #E5E7EB;
        }
        .list-item:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ platform_name }}</h1>
        </div>
        <div class="content">
            {% block content %}{% endblock %}
        </div>
        <div class="footer">
            <p>Need help? <a href="{{ support_url }}">Contact our support team</a></p>
            <p class="unsubscribe">
                <a href="{{ unsubscribe_url }}">Unsubscribe from these emails</a>
            </p>
            <p>&copy; {{ current_year }} {{ platform_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""

    TEMPLATES = {
        "welcome": {
            "subject": "Welcome to {{ platform_name }}, {{ shop_name }}! 🎉",
            "body": """
<h2>Welcome aboard, {{ shop_name }}!</h2>

<p>We're thrilled to have you join the {{ platform_name }} family! Your shop <strong>{{ merchant_domain }}</strong> is now connected and ready to transform your product imagery.</p>

<div class="success">
    <strong>✅ Setup Complete!</strong><br>
    Your shop is successfully connected and ready to start creating stunning product visuals.
</div>

<h3>What's Next?</h3>

<div class="list-item">
    <strong>1. Import Your Products</strong><br>
    We'll automatically sync your product catalog to get you started quickly.
</div>

<div class="list-item">
    <strong>2. Create Your First Visual</strong><br>
    Use our AI-powered tools to generate professional product images and social media content.
</div>

<div class="list-item">
    <strong>3. Explore Features</strong><br>
    Discover background removal, image enhancement, and batch processing capabilities.
</div>

<p style="text-align: center; margin-top: 30px;">
    <a href="{{ platform_name|lower }}.com/dashboard" class="button">Go to Dashboard</a>
</p>

<p>If you have any questions, our support team is here to help you get the most out of {{ platform_name }}.</p>

<p>Here's to creating amazing visuals together! 🚀</p>

<p><strong>The {{ platform_name }} Team</strong></p>
""",
            "variables": {
                "required": ["shop_name", "merchant_domain"],
                "optional": ["merchant_id"],
            },
        },
        "registration_finish": {
            "subject": "✅ Product Import Complete - {{ product_count }} Products Ready!",
            "body": """
<h2>Product Import Successful!</h2>

<p>Great news! We've successfully imported your products to {{ platform_name }}.</p>

<div class="metric">
    <div class="metric-value">{{ product_count }}</div>
    <div class="metric-label">Products Imported</div>
</div>

<p>Your products are now ready for:</p>
<ul>
    <li>✨ AI-powered background removal</li>
    <li>🎨 Professional image enhancement</li>
    <li>📱 Social media content creation</li>
    <li>🚀 Batch processing and automation</li>
</ul>

<p style="text-align: center; margin-top: 30px;">
    <a href="{{ platform_name|lower }}.com/products" class="button">View Your Products</a>
</p>

<p>Tip: Start with your best-selling products to maximize impact!</p>
""",
            "variables": {"required": ["product_count"], "optional": []},
        },
        "registration_sync": {
            "subject": "📊 Product Sync Update - {{ added_count + updated_count }} Changes Detected",
            "body": """
<h2>Product Catalog Sync Complete</h2>

<p>We've just finished syncing your product catalog with the latest changes from your shop.</p>

<h3>Sync Summary</h3>

<table>
    <tr>
        <th>Action</th>
        <th>Count</th>
    </tr>
    <tr>
        <td>✅ New Products Added</td>
        <td><strong>{{ added_count }}</strong></td>
    </tr>
    <tr>
        <td>🔄 Products Updated</td>
        <td><strong>{{ updated_count }}</strong></td>
    </tr>
    {% if removed_count %}
    <tr>
        <td>🗑️ Products Removed</td>
        <td><strong>{{ removed_count }}</strong></td>
    </tr>
    {% endif %}
</table>

{% if added_count > 0 %}
<div class="success">
    <strong>New Products Ready!</strong><br>
    Your {{ added_count }} new products are ready for visual content creation.
</div>
{% endif %}

<p>All changes have been automatically applied to your {{ platform_name }} catalog.</p>

<p style="text-align: center; margin-top: 30px;">
    <a href="{{ platform_name|lower }}.com/products?filter=recent" class="button">View Updated Products</a>
</p>
""",
            "variables": {
                "required": ["added_count", "updated_count"],
                "optional": ["removed_count"],
            },
        },
        "billing_expired": {
            "subject": "⚠️ Subscription Expired - Action Required",
            "body": """
<h2>Your Subscription Has Expired</h2>

<div class="error">
    <strong>Important:</strong> Your {{ plan_name }} subscription has expired. Your account features are currently limited.
</div>

<p>To continue enjoying all {{ platform_name }} features, please renew your subscription.</p>

<h3>What This Means:</h3>
<ul>
    <li>❌ New image generation is paused</li>
    <li>❌ Batch processing is unavailable</li>
    <li>❌ API access is suspended</li>
    <li>✅ Your existing images remain accessible</li>
    <li>✅ Your product catalog is preserved</li>
</ul>

<p style="text-align: center; margin-top: 30px;">
    <a href="{{ renewal_link }}" class="button">Renew Subscription</a>
</p>

<p>Don't lose your momentum! Renew now to continue creating amazing product visuals.</p>

<p>If you have any questions about your subscription or need assistance, please contact our support team.</p>
""",
            "variables": {"required": ["plan_name", "renewal_link"], "optional": []},
        },
        "billing_changed": {
            "subject": "✅ Subscription Updated to {{ plan_name }}",
            "body": """
<h2>Subscription Successfully Updated</h2>

<div class="success">
    <strong>Confirmed!</strong> You're now on the {{ plan_name }} plan.
</div>

<p>Your subscription has been updated and all features associated with your new plan are now active.</p>

<h3>What's Included in {{ plan_name }}:</h3>
<div class="metric">
    <p>✅ Enhanced processing limits<br>
    ✅ Priority support<br>
    ✅ Advanced features<br>
    ✅ API access<br>
    ✅ Bulk operations</p>
</div>

<p style="text-align: center; margin-top: 30px;">
    <a href="{{ platform_name|lower }}.com/billing" class="button">View Billing Details</a>
</p>

<p>Thank you for choosing {{ platform_name }}! We're excited to support your business growth.</p>
""",
            "variables": {"required": ["plan_name"], "optional": []},
        },
        "billing_low_credits": {
            "subject": "⚠️ Low Credit Balance - {{ days_remaining }} Days Remaining",
            "body": """
<h2>Credit Balance Running Low</h2>

<div class="warning">
    <strong>Attention Required:</strong> Your credit balance is running low and may be depleted soon.
</div>

<h3>Current Status:</h3>

<div class="metric">
    <div class="metric-value">${{ current_balance }}</div>
    <div class="metric-label">Current Balance</div>
</div>

<table>
    <tr>
        <td><strong>Estimated Days Remaining:</strong></td>
        <td>{{ days_remaining }} days</td>
    </tr>
    <tr>
        <td><strong>Expected Depletion Date:</strong></td>
        <td>{{ expected_depletion_date }}</td>
    </tr>
</table>

<p>To ensure uninterrupted service, please add credits to your account before they run out.</p>

<p style="text-align: center; margin-top: 30px;">
    <a href="{{ billing_link }}" class="button">Add Credits Now</a>
</p>

<h3>What Happens When Credits Run Out?</h3>
<ul>
    <li>Image generation will be paused</li>
    <li>API requests will be limited</li>
    <li>Batch operations will be unavailable</li>
</ul>

<p>Don't let your creative flow stop! Add credits now to continue creating amazing visuals.</p>
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
        },
        "billing_zero_balance": {
            "subject": "🚨 Urgent: Zero Balance - Service Deactivation Pending",
            "body": """
<h2>Your Credit Balance is Now Zero</h2>

<div class="error">
    <strong>Immediate Action Required!</strong><br>
    Your credit balance has reached zero. Services will be deactivated at <strong>{{ deactivation_time }}</strong>.
</div>

<p>To prevent service interruption, please add credits to your account immediately.</p>

<div class="metric">
    <div class="metric-value">$0.00</div>
    <div class="metric-label">Current Balance</div>
</div>

<h3>⏰ Deactivation Timeline:</h3>
<p><strong>{{ deactivation_time }}</strong> - All premium features will be disabled</p>

<p style="text-align: center; margin-top: 30px;">
    <a href="{{ billing_link }}" class="button">Add Credits Urgently</a>
</p>

<h3>Services at Risk:</h3>
<ul>
    <li>❌ Image generation and processing</li>
    <li>❌ API access</li>
    <li>❌ Batch operations</li>
    <li>❌ New product imports</li>
</ul>

<p><strong>Act now to avoid disruption to your workflow!</strong></p>
""",
            "variables": {
                "required": ["deactivation_time", "billing_link"],
                "optional": [],
            },
        },
        "billing_deactivated": {
            "subject": "❌ Services Deactivated - {{ reason|title }}",
            "body": """
<h2>Services Have Been Deactivated</h2>

<div class="error">
    <strong>Service Status:</strong> Your {{ platform_name }} services have been deactivated due to <strong>{{ reason }}</strong>.
</div>

<h3>Currently Unavailable:</h3>
<ul>
    <li>❌ Image generation and processing</li>
    <li>❌ API access</li>
    <li>❌ Batch operations</li>
    <li>❌ Product catalog updates</li>
</ul>

<h3>Still Available:</h3>
<ul>
    <li>✅ Access to existing images</li>
    <li>✅ Download your data</li>
    <li>✅ View your product catalog</li>
    <li>✅ Account settings</li>
</ul>

<p>To restore full access to all features, please resolve the billing issue.</p>

<p style="text-align: center; margin-top: 30px;">
    <a href="{{ reactivation_link }}" class="button">Reactivate Services</a>
</p>

<p>We value your business and hope to have you back soon. If you need assistance or have questions about your account, our support team is here to help.</p>
""",
            "variables": {"required": ["reason", "reactivation_link"], "optional": []},
        },
    }

    @classmethod
    def get_template(cls, notification_type: str) -> Dict[str, Any]:
        """Get template for notification type"""
        if notification_type not in cls.TEMPLATES:
            raise ValueError(f"Unknown notification type: {notification_type}")

        template = cls.TEMPLATES[notification_type].copy()

        # Wrap body in base template
        template["body"] = cls.BASE_TEMPLATE.replace(
            "{% block content %}{% endblock %}", template["body"]
        )

        return template

    @classmethod
    def get_all_types(cls) -> list:
        """Get all available notification types"""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def validate_variables(
        cls, notification_type: str, provided_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that required variables are provided"""
        if notification_type not in cls.TEMPLATES:
            raise ValueError(f"Unknown notification type: {notification_type}")

        template_vars = cls.TEMPLATES[notification_type]["variables"]
        required = set(template_vars["required"])
        optional = set(template_vars["optional"])
        provided = set(provided_variables.keys())

        # Global variables that are always available
        global_vars = {
            "unsubscribe_url",
            "support_url",
            "current_year",
            "platform_name",
        }

        missing_required = required - provided
        unused_variables = provided - required - optional - global_vars

        return {
            "is_valid": len(missing_required) == 0,
            "missing_required": list(missing_required),
            "unused_variables": list(unused_variables),
            "all_variables": list(required | optional | global_vars),
        }
