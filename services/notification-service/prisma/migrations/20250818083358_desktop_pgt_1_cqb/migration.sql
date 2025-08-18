-- CreateTable
CREATE TABLE "notifications" (
    "id" UUID NOT NULL,
    "merchant_id" UUID NOT NULL,
    "platform_name" VARCHAR(255) NOT NULL,
    "platform_id" VARCHAR(255) NOT NULL,
    "platform_domain" VARCHAR(255) NOT NULL,
    "recipient_email" VARCHAR(255) NOT NULL,
    "template_type" VARCHAR(100) NOT NULL,
    "subject" TEXT NOT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'pending',
    "provider" VARCHAR(50),
    "provider_message_id" VARCHAR(255),
    "error_message" TEXT,
    "retry_count" INTEGER NOT NULL DEFAULT 0,
    "trigger_event" VARCHAR(255) NOT NULL,
    "trigger_event_id" VARCHAR(100),
    "idempotency_key" VARCHAR(255) NOT NULL,
    "template_variables" JSON,
    "extra_metadata" JSON,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "sent_at" TIMESTAMPTZ(3),
    "failed_at" TIMESTAMPTZ(3),

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "notifications_provider_message_id_key" ON "notifications"("provider_message_id");

-- CreateIndex
CREATE UNIQUE INDEX "notifications_idempotency_key_key" ON "notifications"("idempotency_key");

-- CreateIndex
CREATE INDEX "notifications_merchant_id_created_at_idx" ON "notifications"("merchant_id", "created_at");

-- CreateIndex
CREATE INDEX "notifications_platform_name_platform_id_idx" ON "notifications"("platform_name", "platform_id");

-- CreateIndex
CREATE INDEX "notifications_platform_domain_idx" ON "notifications"("platform_domain");

-- CreateIndex
CREATE INDEX "notifications_status_idx" ON "notifications"("status");

-- CreateIndex
CREATE INDEX "notifications_template_type_idx" ON "notifications"("template_type");

-- CreateIndex
CREATE INDEX "notifications_idempotency_key_idx" ON "notifications"("idempotency_key");
