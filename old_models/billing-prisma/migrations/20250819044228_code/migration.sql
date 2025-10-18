-- CreateEnum
CREATE TYPE "PurchaseStatus" AS ENUM ('pending', 'completed', 'failed', 'expired');

-- CreateTable
CREATE TABLE "billing_records" (
    "id" UUID NOT NULL,
    "merchant_id" UUID NOT NULL,
    "trial_available" BOOLEAN NOT NULL DEFAULT true,
    "trial_started_at" TIMESTAMPTZ(3),
    "trial_ends_at" TIMESTAMPTZ(3),
    "total_credits_purchased" INTEGER NOT NULL DEFAULT 0,
    "last_purchase_at" TIMESTAMPTZ(3),
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "billing_records_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "credit_purchases" (
    "id" UUID NOT NULL,
    "merchant_id" UUID NOT NULL,
    "credits" INTEGER NOT NULL,
    "amount" TEXT NOT NULL,
    "status" "PurchaseStatus" NOT NULL DEFAULT 'pending',
    "platform" TEXT,
    "platform_charge_id" TEXT,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completed_at" TIMESTAMPTZ(3),
    "expires_at" TIMESTAMPTZ(3),

    CONSTRAINT "credit_purchases_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "billing_records_merchant_id_key" ON "billing_records"("merchant_id");

-- CreateIndex
CREATE INDEX "billing_records_trial_ends_at_idx" ON "billing_records"("trial_ends_at");

-- CreateIndex
CREATE UNIQUE INDEX "credit_purchases_platform_charge_id_key" ON "credit_purchases"("platform_charge_id");

-- CreateIndex
CREATE INDEX "credit_purchases_merchant_id_idx" ON "credit_purchases"("merchant_id");

-- CreateIndex
CREATE INDEX "credit_purchases_status_idx" ON "credit_purchases"("status");

-- CreateIndex
CREATE INDEX "credit_purchases_platform_charge_id_idx" ON "credit_purchases"("platform_charge_id");

-- AddForeignKey
ALTER TABLE "credit_purchases" ADD CONSTRAINT "credit_purchases_merchant_id_fkey" FOREIGN KEY ("merchant_id") REFERENCES "billing_records"("merchant_id") ON DELETE RESTRICT ON UPDATE CASCADE;
