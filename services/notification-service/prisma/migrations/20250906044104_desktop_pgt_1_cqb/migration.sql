/*
  Warnings:

  - You are about to drop the column `created_at` on the `notifications` table. All the data in the column will be lost.
  - You are about to drop the column `updated_at` on the `notifications` table. All the data in the column will be lost.
  - You are about to drop the `notification_attempts` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "notification_attempts" DROP CONSTRAINT "notification_attempts_notification_id_fkey";

-- DropIndex
DROP INDEX "notifications_idempotency_key_idx";

-- DropIndex
DROP INDEX "notifications_merchant_id_created_at_idx";

-- DropIndex
DROP INDEX "notifications_platform_name_platform_shop_id_idx";

-- DropIndex
DROP INDEX "notifications_status_created_at_idx";

-- DropIndex
DROP INDEX "notifications_template_type_idx";

-- AlterTable
ALTER TABLE "notifications" DROP COLUMN "created_at",
DROP COLUMN "updated_at",
ADD COLUMN     "attempt_count" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "delivered_at" TIMESTAMPTZ(3),
ADD COLUMN     "first_attempt_at" TIMESTAMPTZ(3),
ADD COLUMN     "last_attempt_at" TIMESTAMPTZ(3),
ADD COLUMN     "provider_message" JSON;

-- DropTable
DROP TABLE "notification_attempts";

-- DropEnum
DROP TYPE "AttemptStatus";

-- CreateIndex
CREATE INDEX "notifications_merchant_id_first_attempt_at_idx" ON "notifications"("merchant_id", "first_attempt_at");

-- CreateIndex
CREATE INDEX "notifications_status_last_attempt_at_idx" ON "notifications"("status", "last_attempt_at");
