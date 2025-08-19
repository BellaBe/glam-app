from uuid import UUID


from shared.utils.logger import ServiceLogger

from ..config import ServiceConfig
from ..events.publishers import BillingEventPublisher
from ..exceptions import InvalidCreditPackError, MerchantNotFoundError, PlatformCheckoutError, PurchaseNotFoundError
from ..repositories.billing_repository import BillingRepository
from ..repositories.purchase_repository import PurchaseRepository
from ..schemas.billing import CreditsPurchasedPayload, Platform, PurchaseCreatedOut, PurchaseCreateIn, PurchaseOut
from ..utils.credit_packs import CreditPackManager
from ..utils.shopify_client import ShopifyClient


class PurchaseService:
    """Service for purchase operations"""

    def __init__(
        self,
        config: ServiceConfig,
        billing_repo: BillingRepository,
        purchase_repo: PurchaseRepository,
        pack_manager: CreditPackManager,
        shopify_client: ShopifyClient,
        publisher: BillingEventPublisher,
        logger: ServiceLogger,
    ):
        self.config = config
        self.billing_repo = billing_repo
        self.purchase_repo = purchase_repo
        self.pack_manager = pack_manager
        self.shopify_client = shopify_client
        self.publisher = publisher
        self.logger = logger

    async def create_purchase(self, merchant_id: UUID, shop_domain: str, data: PurchaseCreateIn) -> PurchaseCreatedOut:
        """Create credit purchase"""
        # Validate merchant exists
        billing_record = await self.billing_repo.find_by_merchant_id(merchant_id)
        if not billing_record:
            raise MerchantNotFoundError(str(merchant_id))

        # Get pack details
        pack = self.pack_manager.get_pack(data.pack)
        if not pack:
            raise InvalidCreditPackError(data.pack.value)

        # Create purchase record
        purchase = await self.purchase_repo.create(
            merchant_id=merchant_id,
            credits=pack["credits"],
            amount=pack["price"],
            platform=data.platform.value,
            expiry_hours=self.config.pending_purchase_expiry_hours,
        )

        # Create platform-specific checkout
        checkout_url = None
        charge_id = None

        if data.platform == Platform.SHOPIFY:
            try:
                result = await self.shopify_client.create_charge(
                    shop_domain=shop_domain,
                    amount=pack["price"],
                    name=f"{pack['credits']} Credits Pack",
                    return_url=data.return_url,
                )
                checkout_url = result["confirmation_url"]
                charge_id = result["charge_id"]

                # Update purchase with charge ID
                await self.purchase_repo.update_platform_charge_id(UUID(purchase.id), charge_id)

            except Exception as e:
                # Mark purchase as failed
                await self.purchase_repo.fail_purchase(UUID(purchase.id))
                raise PlatformCheckoutError(data.platform.value, str(e)) from e
        else:
            # Other platforms not implemented yet
            await self.purchase_repo.fail_purchase(UUID(purchase.id))
            raise PlatformCheckoutError(data.platform.value, "Platform not supported")

        return PurchaseCreatedOut(
            purchase_id=UUID(purchase.id), checkout_url=checkout_url, expires_at=purchase.expires_at
        )

    async def get_purchase(self, purchase_id: UUID) -> PurchaseOut:
        """Get purchase by ID"""
        purchase = await self.purchase_repo.find_by_id(purchase_id)
        if not purchase:
            raise PurchaseNotFoundError(str(purchase_id))

        return PurchaseOut.model_validate(purchase)

    async def list_purchases(self, merchant_id: UUID, limit: int = 10) -> list[PurchaseOut]:
        """List purchases for merchant"""
        purchases = await self.purchase_repo.find_by_merchant(merchant_id, limit)
        return [PurchaseOut.model_validate(p) for p in purchases]

    async def handle_purchase_webhook(self, charge_id: str, status: str, merchant_id: UUID) -> None:
        """Handle purchase webhook from platform"""
        # Find purchase by charge ID
        purchase = await self.purchase_repo.find_by_charge_id(charge_id)
        if not purchase:
            self.logger.warning(f"Purchase not found for charge {charge_id}")
            return

        # Skip if already processed
        if purchase.status != "pending":
            self.logger.info(f"Purchase {purchase.id} already processed")
            return

        # Process based on status
        if status == "accepted" or status == "active":
            # Mark as completed
            purchase = await self.purchase_repo.complete_purchase(UUID(purchase.id))

            # Update billing record totals
            await self.billing_repo.update_purchase_totals(UUID(purchase.merchant_id), purchase.credits)

            # Publish event
            await self.publisher.credits_purchased(
                CreditsPurchasedPayload(
                    merchant_id=UUID(purchase.merchant_id),
                    purchase_id=UUID(purchase.id),
                    credits=purchase.credits,
                    amount=purchase.amount,
                    platform=purchase.platform,
                )
            )

            self.logger.info(f"Purchase {purchase.id} completed successfully")

        else:
            # Mark as failed
            await self.purchase_repo.fail_purchase(UUID(purchase.id))
            self.logger.info(f"Purchase {purchase.id} failed with status {status}")

    async def expire_pending_purchases(self) -> None:
        """Expire pending purchases past expiry time (cron job)"""
        count = await self.purchase_repo.expire_pending_purchases()
        if count > 0:
            self.logger.info(f"Expired {count} pending purchases")
