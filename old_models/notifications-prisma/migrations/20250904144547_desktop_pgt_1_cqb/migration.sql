-- CreateEnum
CREATE TYPE "NotificationStatus" AS ENUM ('pending', 'sent', 'failed');

-- CreateEnum
CREATE TYPE "AttemptStatus" AS ENUM ('success', 'failed', 'timeout');

-- CreateTable
CREATE TABLE "notifications" (
    "id" UUID NOT NULL,
    "merchant_id" UUID NOT NULL,
    "platform_name" VARCHAR(255) NOT NULL,
    "platform_shop_id" VARCHAR(255) NOT NULL,
    "domain" VARCHAR(255) NOT NULL,
    "recipient_email" VARCHAR(255) NOT NULL,
    "template_type" VARCHAR(100) NOT NULL,
    "template_variables" JSON NOT NULL,
    "status" "NotificationStatus" NOT NULL DEFAULT 'pending',
    "provider_message_id" VARCHAR(255),
    "idempotency_key" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "notification_attempts" (
    "id" UUID NOT NULL,
    "notification_id" UUID NOT NULL,
    "attempt_number" INTEGER NOT NULL,
    "provider" VARCHAR(50) NOT NULL,
    "status" "AttemptStatus" NOT NULL,
    "error_message" TEXT,
    "provider_response" JSON,
    "attempted_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notification_attempts_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "notifications_provider_message_id_key" ON "notifications"("provider_message_id");

-- CreateIndex
CREATE UNIQUE INDEX "notifications_idempotency_key_key" ON "notifications"("idempotency_key");

-- CreateIndex
CREATE INDEX "notifications_merchant_id_created_at_idx" ON "notifications"("merchant_id", "created_at");

-- CreateIndex
CREATE INDEX "notifications_platform_name_platform_shop_id_idx" ON "notifications"("platform_name", "platform_shop_id");

-- CreateIndex
CREATE INDEX "notifications_status_created_at_idx" ON "notifications"("status", "created_at");

-- CreateIndex
CREATE INDEX "notifications_template_type_idx" ON "notifications"("template_type");

-- CreateIndex
CREATE INDEX "notifications_idempotency_key_idx" ON "notifications"("idempotency_key");

-- CreateIndex
CREATE INDEX "notification_attempts_notification_id_attempt_number_idx" ON "notification_attempts"("notification_id", "attempt_number");

-- CreateIndex
CREATE UNIQUE INDEX "notification_attempts_notification_id_attempt_number_key" ON "notification_attempts"("notification_id", "attempt_number");

-- AddForeignKey
ALTER TABLE "notification_attempts" ADD CONSTRAINT "notification_attempts_notification_id_fkey" FOREIGN KEY ("notification_id") REFERENCES "notifications"("id") ON DELETE CASCADE ON UPDATE CASCADE;
