-- CreateEnum
CREATE TYPE "MerchantStatus" AS ENUM ('PENDING', 'ACTIVE', 'PAUSED', 'SUSPENDED', 'UNINSTALLED');

-- CreateTable
CREATE TABLE "merchants" (
    "id" UUID NOT NULL,
    "platform_name" TEXT NOT NULL,
    "platform_id" TEXT NOT NULL,
    "platform_domain" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "primary_domain" TEXT,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "country" TEXT,
    "platform_version" TEXT NOT NULL,
    "scopes" TEXT,
    "status" "MerchantStatus" NOT NULL DEFAULT 'PENDING',
    "status_changed_at" TIMESTAMP(3),
    "installed_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "uninstalled_at" TIMESTAMP(3),
    "last_sync_at" TIMESTAMP(3),
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "merchants_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "merchants_platform_id_platform_domain_idx" ON "merchants"("platform_id", "platform_domain");

-- CreateIndex
CREATE INDEX "merchants_platform_domain_idx" ON "merchants"("platform_domain");

-- CreateIndex
CREATE INDEX "merchants_status_idx" ON "merchants"("status");

-- CreateIndex
CREATE UNIQUE INDEX "merchants_platform_name_platform_id_key" ON "merchants"("platform_name", "platform_id");

-- CreateIndex
CREATE UNIQUE INDEX "merchants_platform_name_platform_domain_key" ON "merchants"("platform_name", "platform_domain");
