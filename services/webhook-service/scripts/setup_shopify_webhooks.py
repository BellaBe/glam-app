# services/webhook-service/scripts/setup_shopify_webhooks.py
#!/usr/bin/env python3
"""
Script to set up Shopify webhooks for development.

This script helps configure Shopify webhooks to point to your local
webhook service during development.
"""

import requests
import json
import os
from typing import Dict, List, Optional


class ShopifyWebhookManager:
    """Manages Shopify webhook configuration."""
    
    def __init__(self, shop_domain: str, access_token: str):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.base_url = f"https://{shop_domain}/admin/api/2024-01"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
    
    def list_webhooks(self) -> List[Dict]:
        """List all existing webhooks."""
        
        response = requests.get(
            f"{self.base_url}/webhooks.json",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json().get("webhooks", [])
        else:
            print(f"Failed to list webhooks: {response.status_code} - {response.text}")
            return []
    
    def create_webhook(self, topic: str, address: str) -> bool:
        """Create a new webhook."""
        
        webhook_data = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/webhooks.json",
            headers=self.headers,
            json=webhook_data
        )
        
        if response.status_code == 201:
            webhook = response.json()["webhook"]
            print(f"✅ Created webhook: {topic} -> {address} (ID: {webhook['id']})")
            return True
        else:
            print(f"❌ Failed to create webhook for {topic}: {response.status_code} - {response.text}")
            return False
    
    def delete_webhook(self, webhook_id: int) -> bool:
        """Delete a webhook."""
        
        response = requests.delete(
            f"{self.base_url}/webhooks/{webhook_id}.json",
            headers=self.headers
        )
        
        if response.status_code == 200:
            print(f"🗑️  Deleted webhook ID: {webhook_id}")
            return True
        else:
            print(f"❌ Failed to delete webhook {webhook_id}: {response.status_code} - {response.text}")
            return False
    
    def setup_development_webhooks(self, webhook_service_url: str) -> None:
        """Set up webhooks for development."""
        
        # Define the webhooks we want to create
        webhook_topics = [
            "app/uninstalled",
            "orders/create",
            "orders/updated",
            "orders/fulfilled",
            "orders/cancelled",
            "products/create",
            "products/update",
            "products/delete",
            "inventory_levels/update",
            "inventory_items/update",
            "customers/data_request",
            "customers/redact",
            "shop/redact"
        ]
        
        print(f"🔧 Setting up webhooks for {self.shop_domain}")
        print(f"📡 Webhook service URL: {webhook_service_url}")
        print()
        
        # List existing webhooks
        existing_webhooks = self.list_webhooks()
        print(f"📋 Found {len(existing_webhooks)} existing webhooks")
        
        # Create webhooks for each topic
        success_count = 0
        for topic in webhook_topics:
            # Convert topic format (e.g., "orders/create" -> "orders/create")
            webhook_url = f"{webhook_service_url}/webhooks/shopify/{topic.replace('/', '%2F')}"
            
            # Check if webhook already exists
            exists = any(
                webhook["topic"] == topic and webhook["address"] == webhook_url
                for webhook in existing_webhooks
            )
            
            if exists:
                print(f"⏭️  Webhook already exists: {topic}")
                success_count += 1
            else:
                if self.create_webhook(topic, webhook_url):
                    success_count += 1
        
        print()
        print(f"🎯 Successfully configured {success_count}/{len(webhook_topics)} webhooks")
    
    def cleanup_webhooks(self, webhook_service_url: str) -> None:
        """Clean up webhooks pointing to the webhook service."""
        
        existing_webhooks = self.list_webhooks()
        
        webhooks_to_delete = [
            webhook for webhook in existing_webhooks
            if webhook["address"].startswith(webhook_service_url)
        ]
        
        if not webhooks_to_delete:
            print("🧹 No webhooks to clean up")
            return
        
        print(f"🧹 Cleaning up {len(webhooks_to_delete)} webhooks")
        
        for webhook in webhooks_to_delete:
            self.delete_webhook(webhook["id"])
        
        print("✅ Cleanup complete")


def main():
    """Main function to set up Shopify webhooks."""
    
    # Configuration
    shop_domain = os.getenv("SHOPIFY_SHOP_DOMAIN", "your-shop.myshopify.com")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    webhook_service_url = os.getenv("WEBHOOK_SERVICE_URL", "https://your-ngrok-url.ngrok.io")
    
    if not access_token:
        print("❌ SHOPIFY_ACCESS_TOKEN environment variable is required")
        print("   Get this from your Shopify app configuration")
        return
    
    if "your-shop" in shop_domain:
        print("❌ Please set SHOPIFY_SHOP_DOMAIN environment variable")
        print("   Example: export SHOPIFY_SHOP_DOMAIN=your-shop.myshopify.com")
        return
    
    if "ngrok" in webhook_service_url and "your-ngrok" in webhook_service_url:
        print("❌ Please set WEBHOOK_SERVICE_URL environment variable")
        print("   Example: export WEBHOOK_SERVICE_URL=https://abc123.ngrok.io")
        return
    
    # Initialize manager
    manager = ShopifyWebhookManager(shop_domain, access_token)
    
    # Show current webhooks
    print("📋 Current webhooks:")
    webhooks = manager.list_webhooks()
    for webhook in webhooks:
        print(f"   {webhook['topic']} -> {webhook['address']}")
    print()
    
    # Ask user what to do
    action = input("What would you like to do? (setup/cleanup/list): ").strip().lower()
    
    if action == "setup":
        manager.setup_development_webhooks(webhook_service_url)
    elif action == "cleanup":
        manager.cleanup_webhooks(webhook_service_url)
    elif action == "list":
        print("📋 All webhooks listed above")
    else:
        print("❌ Invalid action. Use 'setup', 'cleanup', or 'list'")


if __name__ == "__main__":
    main()