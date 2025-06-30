# services/notification-service/src/database/seed_templates.py
"""Seed script to initialize email templates in the database"""

import asyncio
import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ..models.notification_template import NotificationTemplate
from ..templates.email_templates import EmailTemplates


class TemplateSeedService:
    """Service to seed email templates into the database"""
    
    def __init__(self, database_url: str):
        """Initialize seed service with database connection"""
        self.database_url = database_url
        self.engine = create_async_engine(database_url)
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    async def seed_templates(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Seed all email templates into the database
        
        Args:
            force_update: If True, updates existing templates. If False, only adds new ones.
        
        Returns:
            Dictionary with seeding results
        """
        results = {
            "created": [],
            "updated": [],
            "skipped": [],
            "errors": []
        }
        
        async with self.async_session() as session:
            try:
                # Get all templates from EmailTemplates class
                all_templates = EmailTemplates.get_all_templates()
                
                for template_type, template_data in all_templates.items():
                    try:
                        # Check if template already exists
                        existing = await session.query(NotificationTemplate).filter_by(
                            name=f"{template_type}_email"
                        ).first()
                        
                        if existing and not force_update:
                            results["skipped"].append(template_type)
                            continue
                        
                        if existing and force_update:
                            # Update existing template
                            existing.subject_template = template_data["subject"]
                            existing.body_template = template_data["body"]
                            existing.variables = template_data.get("variables", {
                                "required": [],
                                "optional": []
                            })
                            existing.updated_at = datetime.utcnow()
                            
                            results["updated"].append(template_type)
                        else:
                            # Create new template
                            new_template = NotificationTemplate(
                                id=str(uuid4()),
                                name=f"{template_type}_email",
                                type=template_type,
                                subject_template=template_data["subject"],
                                body_template=template_data["body"],
                                variables=template_data.get("variables", {
                                    "required": [],
                                    "optional": []
                                }),
                                description=self._get_template_description(template_type),
                                is_active=True,
                                created_by="system_seed",
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                            
                            session.add(new_template)
                            results["created"].append(template_type)
                    
                    except Exception as e:
                        results["errors"].append({
                            "template": template_type,
                            "error": str(e)
                        })
                
                # Commit all changes
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                results["errors"].append({
                    "template": "general",
                    "error": f"Database error: {str(e)}"
                })
        
        return results
    
    def _get_template_description(self, template_type: str) -> str:
        """Get description for each template type"""
        descriptions = {
            "welcome": "Welcome email sent when a shop launches GlamYouUp",
            "registration_finish": "Notification sent when product registration is completed",
            "registration_sync": "Update notification after product catalog synchronization",
            "billing_expired": "Alert sent when subscription expires",
            "billing_changed": "Confirmation when billing plan is updated",
            "billing_low_credits": "Warning when credit balance is running low",
            "billing_zero_balance": "Urgent alert when balance reaches zero",
            "billing_deactivated": "Notification when features are deactivated"
        }
        
        return descriptions.get(template_type, f"Email template for {template_type}")
    
    async def verify_templates(self) -> List[Dict[str, Any]]:
        """Verify all templates are properly seeded"""
        templates = []
        
        async with self.async_session() as session:
            results = await session.query(NotificationTemplate).filter_by(
                is_active=True
            ).all()
            
            for template in results:
                templates.append({
                    "id": template.id,
                    "name": template.name,
                    "type": template.type,
                    "variables": template.variables,
                    "is_active": template.is_active,
                    "created_at": template.created_at.isoformat()
                })
        
        return templates
    
    async def export_templates(self, output_file: str = "templates_export.json"):
        """Export all templates to a JSON file for backup"""
        templates = await self.verify_templates()
        
        with open(output_file, 'w') as f:
            json.dump({
                "export_date": datetime.utcnow().isoformat(),
                "templates": templates
            }, f, indent=2)
        
        return f"Exported {len(templates)} templates to {output_file}"


# CLI Script
async def main():
    """Main function to run the seed script"""
    import argparse
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Seed email templates to database")
    parser.add_argument(
        "--force-update", 
        action="store_true", 
        help="Force update existing templates"
    )
    parser.add_argument(
        "--verify", 
        action="store_true", 
        help="Verify templates after seeding"
    )
    parser.add_argument(
        "--export", 
        action="store_true", 
        help="Export templates to JSON file"
    )
    parser.add_argument(
        "--database-url", 
        default=os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/notifications"),
        help="Database connection URL"
    )
    
    args = parser.parse_args()
    
    # Initialize seeder
    seeder = TemplateSeedService(args.database_url)
    
    # Seed templates
    print("🌱 Seeding email templates...")
    results = await seeder.seed_templates(force_update=args.force_update)
    
    print("\n📊 Seeding Results:")
    print(f"  ✅ Created: {len(results['created'])} templates")
    if results['created']:
        print(f"     {', '.join(results['created'])}")
    
    print(f"  📝 Updated: {len(results['updated'])} templates")
    if results['updated']:
        print(f"     {', '.join(results['updated'])}")
    
    print(f"  ⏭️  Skipped: {len(results['skipped'])} templates")
    if results['skipped']:
        print(f"     {', '.join(results['skipped'])}")
    
    if results['errors']:
        print(f"  ❌ Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"     {error['template']}: {error['error']}")
    
    # Verify if requested
    if args.verify:
        print("\n🔍 Verifying templates...")
        templates = await seeder.verify_templates()
        print(f"Found {len(templates)} active templates:")
        for template in templates:
            print(f"  - {template['type']}: {template['name']}")
    
    # Export if requested
    if args.export:
        print("\n📦 Exporting templates...")
        export_result = await seeder.export_templates()
        print(f"  {export_result}")
    
    # Close connection
    await seeder.engine.dispose()
    print("\n✨ Done!")


if __name__ == "__main__":
    asyncio.run(main())