-- CreateEnum
CREATE TYPE "MerchantStatus" AS ENUM ('PENDING', 'ONBOARDING', 'TRIAL', 'ACTIVE', 'SUSPENDED', 'DEACTIVATED');

-- CreateTable
CREATE TABLE "merchants" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "shop_id" TEXT NOT NULL,
    "shop_domain" TEXT NOT NULL,
    "shop_name" TEXT NOT NULL,
    "shop_url" TEXT,
    "shopify_access_token" TEXT NOT NULL,
    "platform_api_version" TEXT NOT NULL DEFAULT '2024-01',
    "email" TEXT NOT NULL,
    "phone" TEXT,
    "timezone" TEXT NOT NULL DEFAULT 'UTC',
    "country" TEXT,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "language" TEXT NOT NULL DEFAULT 'en',
    "plan_name" TEXT,
    "platform" TEXT NOT NULL DEFAULT 'shopify',
    "onboarding_completed" BOOLEAN NOT NULL DEFAULT false,
    "onboarding_step" TEXT,

    CONSTRAINT "merchants_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "merchant_statuses" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "merchant_id" TEXT NOT NULL,
    "status" "MerchantStatus" NOT NULL,
    "previous_status" "MerchantStatus",
    "status_reason" TEXT,
    "changed_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "activated_at" TIMESTAMP(3),
    "suspended_at" TIMESTAMP(3),
    "deactivated_at" TIMESTAMP(3),
    "last_activity_at" TIMESTAMP(3),
    "status_history" JSONB NOT NULL DEFAULT '[]',

    CONSTRAINT "merchant_statuses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "merchant_configurations" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "merchant_id" TEXT NOT NULL,
    "terms_accepted" BOOLEAN NOT NULL DEFAULT false,
    "terms_accepted_at" TIMESTAMP(3),
    "terms_version" TEXT,
    "privacy_accepted" BOOLEAN NOT NULL DEFAULT false,
    "privacy_accepted_at" TIMESTAMP(3),
    "privacy_version" TEXT,
    "widget_enabled" BOOLEAN NOT NULL DEFAULT true,
    "widget_position" TEXT NOT NULL DEFAULT 'bottom-right',
    "widget_theme" TEXT NOT NULL DEFAULT 'light',
    "widget_language" TEXT NOT NULL DEFAULT 'auto',
    "widget_configuration" JSONB NOT NULL DEFAULT '{}',
    "api_rate_limits" JSONB NOT NULL DEFAULT '{}',
    "webhook_configuration" JSONB NOT NULL DEFAULT '{}',
    "integration_settings" JSONB NOT NULL DEFAULT '{}',
    "custom_css" TEXT,
    "custom_branding" JSONB NOT NULL DEFAULT '{}',
    "custom_messages" JSONB NOT NULL DEFAULT '{}',
    "is_marketable" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "merchant_configurations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "installation_records" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "merchant_id" TEXT NOT NULL,
    "platform" TEXT NOT NULL DEFAULT 'shopify',
    "installed_at" TIMESTAMP(3) NOT NULL,
    "uninstalled_at" TIMESTAMP(3),
    "install_channel" TEXT,
    "installed_by" TEXT,
    "installation_ip" TEXT,
    "app_version" TEXT,
    "platform_api_version" TEXT,
    "permissions_granted" JSONB NOT NULL DEFAULT '[]',
    "callbacks_configured" JSONB NOT NULL DEFAULT '[]',
    "referral_code" TEXT,
    "utm" JSONB NOT NULL DEFAULT '{}',
    "platform_metadata" JSONB NOT NULL DEFAULT '{}',
    "uninstall_reason" TEXT,
    "uninstall_method" TEXT,
    "uninstall_feedback" JSONB NOT NULL DEFAULT '{}',

    CONSTRAINT "installation_records_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "merchants_shop_id_key" ON "merchants"("shop_id");

-- CreateIndex
CREATE INDEX "merchants_shop_id_idx" ON "merchants"("shop_id");

-- CreateIndex
CREATE INDEX "merchants_shop_domain_idx" ON "merchants"("shop_domain");

-- CreateIndex
CREATE INDEX "merchants_email_idx" ON "merchants"("email");

-- CreateIndex
CREATE UNIQUE INDEX "merchant_statuses_merchant_id_key" ON "merchant_statuses"("merchant_id");

-- CreateIndex
CREATE INDEX "merchant_statuses_status_idx" ON "merchant_statuses"("status");

-- CreateIndex
CREATE INDEX "merchant_statuses_merchant_id_idx" ON "merchant_statuses"("merchant_id");

-- CreateIndex
CREATE UNIQUE INDEX "merchant_configurations_merchant_id_key" ON "merchant_configurations"("merchant_id");

-- CreateIndex
CREATE INDEX "merchant_configurations_merchant_id_idx" ON "merchant_configurations"("merchant_id");

-- CreateIndex
CREATE INDEX "installation_records_merchant_id_platform_idx" ON "installation_records"("merchant_id", "platform");

-- CreateIndex
CREATE INDEX "installation_records_platform_installed_at_idx" ON "installation_records"("platform", "installed_at");

-- CreateIndex
CREATE INDEX "installation_records_merchant_id_idx" ON "installation_records"("merchant_id");

-- AddForeignKey
ALTER TABLE "merchant_statuses" ADD CONSTRAINT "merchant_statuses_merchant_id_fkey" FOREIGN KEY ("merchant_id") REFERENCES "merchants"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "merchant_configurations" ADD CONSTRAINT "merchant_configurations_merchant_id_fkey" FOREIGN KEY ("merchant_id") REFERENCES "merchants"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "installation_records" ADD CONSTRAINT "installation_records_merchant_id_fkey" FOREIGN KEY ("merchant_id") REFERENCES "merchants"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
