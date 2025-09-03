-- CreateTable
CREATE TABLE "credit_accounts" (
    "id" UUID NOT NULL,
    "merchant_id" UUID NOT NULL,
    "platform_name" TEXT NOT NULL,
    "platform_id" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "balance" INTEGER NOT NULL DEFAULT 0,
    "total_granted" INTEGER NOT NULL DEFAULT 0,
    "total_consumed" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "credit_accounts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "credit_transactions" (
    "id" UUID NOT NULL,
    "account_id" UUID NOT NULL,
    "merchant_id" UUID NOT NULL,
    "amount" INTEGER NOT NULL,
    "operation" TEXT NOT NULL,
    "balance_before" INTEGER NOT NULL,
    "balance_after" INTEGER NOT NULL,
    "reference_type" TEXT NOT NULL,
    "reference_id" TEXT NOT NULL,
    "description" TEXT,
    "metadata" JSONB,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "credit_transactions_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "credit_accounts_merchant_id_key" ON "credit_accounts"("merchant_id");

-- CreateIndex
CREATE INDEX "credit_accounts_merchant_id_idx" ON "credit_accounts"("merchant_id");

-- CreateIndex
CREATE INDEX "credit_accounts_domain_idx" ON "credit_accounts"("domain");

-- CreateIndex
CREATE INDEX "credit_accounts_platform_name_platform_id_idx" ON "credit_accounts"("platform_name", "platform_id");

-- CreateIndex
CREATE INDEX "credit_transactions_merchant_id_created_at_idx" ON "credit_transactions"("merchant_id", "created_at");

-- CreateIndex
CREATE UNIQUE INDEX "credit_transactions_reference_type_reference_id_key" ON "credit_transactions"("reference_type", "reference_id");
