from shared.messaging.publisher import Publisher


class WebhookEventPublisher(Publisher):
    """Publisher for webhook domain events"""

    @property
    def service_name(self) -> str:
        return "webhook-service"

    async def app_uninstalled(self, domain: str, webhook_id: str, correlation_id: str) -> str:
        """Publish app uninstalled event"""
        return await self.publish_event(
            subject="evt.webhook.app.uninstalled",
            data={"domain": domain, "webhook_id": webhook_id},
            correlation_id=correlation_id,
        )

    async def app_subscription_updated(
        self, domain: str, subscription_id: str, status: str, webhook_id: str, correlation_id: str
    ) -> str:
        """Publish app subscription updated event"""
        return await self.publish_event(
            subject="evt.webhook.app.subscription_updated",
            data={
                "domain": domain,
                "subscription_id": subscription_id,
                "status": status,
                "webhook_id": webhook_id,
            },
            correlation_id=correlation_id,
        )

    async def app_purchase_updated(
        self, domain: str, charge_id: str, status: str, test: bool, webhook_id: str, correlation_id: str
    ) -> str:
        """Publish app purchase updated event"""
        return await self.publish_event(
            subject="evt.webhook.app.purchase_updated",
            data={
                "domain": domain,
                "charge_id": charge_id,
                "status": status,
                "test": test,
                "webhook_id": webhook_id,
            },
            correlation_id=correlation_id,
        )

    async def order_created(
        self,
        domain: str,
        order_id: str,
        total_price: str,
        currency: str,
        created_at: str,
        line_items_count: int,
        webhook_id: str,
        correlation_id: str,
    ) -> str:
        """Publish order created event"""
        return await self.publish_event(
            subject="evt.webhook.order.created",
            data={
                "domain": domain,
                "order_id": order_id,
                "total_price": total_price,
                "currency": currency,
                "created_at": created_at,
                "line_items_count": line_items_count,
                "webhook_id": webhook_id,
            },
            correlation_id=correlation_id,
        )

    async def catalog_product_event(
        self,
        event_type: str,  # created, updated, deleted
        domain: str,
        product_id: str,
        updated_at: str | None,
        webhook_id: str,
        correlation_id: str,
    ) -> str:
        """Publish catalog product event"""
        subject = f"evt.webhook.catalog.product_{event_type}"
        data = {"domain": domain, "product_id": product_id, "webhook_id": webhook_id}
        if updated_at and event_type == "updated":
            data["updated_at"] = updated_at

        return await self.publish_event(subject=subject, data=data, correlation_id=correlation_id)

    async def catalog_collection_event(
        self,
        event_type: str,  # created, updated, deleted
        domain: str,
        collection_id: str,
        updated_at: str | None,
        webhook_id: str,
        correlation_id: str,
    ) -> str:
        """Publish catalog collection event"""
        subject = f"evt.webhook.catalog.collection_{event_type}"
        data = {"domain": domain, "collection_id": collection_id, "webhook_id": webhook_id}
        if updated_at and event_type == "updated":
            data["updated_at"] = updated_at

        return await self.publish_event(subject=subject, data=data, correlation_id=correlation_id)

    async def inventory_updated(
        self,
        domain: str,
        inventory_item_id: str,
        location_id: str,
        available: int,
        webhook_id: str,
        correlation_id: str,
    ) -> str:
        """Publish inventory updated event"""
        return await self.publish_event(
            subject="evt.webhook.inventory.updated",
            data={
                "domain": domain,
                "inventory_item_id": inventory_item_id,
                "location_id": location_id,
                "available": available,
                "webhook_id": webhook_id,
            },
            correlation_id=correlation_id,
        )

    async def gdpr_data_request(
        self, domain: str, customer_id: str, orders_requested: list[str], webhook_id: str, correlation_id: str
    ) -> str:
        """Publish GDPR data request event"""
        return await self.publish_event(
            subject="evt.webhook.gdpr.data_request",
            data={
                "domain": domain,
                "customer_id": customer_id,
                "orders_requested": orders_requested,
                "webhook_id": webhook_id,
            },
            correlation_id=correlation_id,
        )

    async def gdpr_customer_redact(
        self, domain: str, customer_id: str, orders_to_redact: list[str], webhook_id: str, correlation_id: str
    ) -> str:
        """Publish GDPR customer redact event"""
        return await self.publish_event(
            subject="evt.webhook.gdpr.customer_redact",
            data={
                "domain": domain,
                "customer_id": customer_id,
                "orders_to_redact": orders_to_redact,
                "webhook_id": webhook_id,
            },
            correlation_id=correlation_id,
        )

    async def gdpr_shop_redact(self, domain: str, webhook_id: str, correlation_id: str) -> str:
        """Publish GDPR shop redact event"""
        return await self.publish_event(
            subject="evt.webhook.gdpr.shop_redact",
            data={"domain": domain, "webhook_id": webhook_id},
            correlation_id=correlation_id,
        )
