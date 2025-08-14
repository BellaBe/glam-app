-- CreateTable
CREATE TABLE "webhook_entries" (
    "id" UUID NOT NULL,
    "platform" VARCHAR(50) NOT NULL,
    "webhook_id" VARCHAR(255) NOT NULL,
    "topic" VARCHAR(255) NOT NULL,
    "shop_domain" VARCHAR(255) NOT NULL,
    "payload" JSONB NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'RECEIVED',
    "processing_attempts" INTEGER NOT NULL DEFAULT 0,
    "error_message" TEXT,
    "processed_at" TIMESTAMPTZ(3),
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "webhook_entries_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "webhook_entries_webhook_id_key" ON "webhook_entries"("webhook_id");

-- CreateIndex
CREATE INDEX "webhook_entries_shop_domain_topic_idx" ON "webhook_entries"("shop_domain", "topic");

-- CreateIndex
CREATE INDEX "webhook_entries_status_processing_attempts_idx" ON "webhook_entries"("status", "processing_attempts");
