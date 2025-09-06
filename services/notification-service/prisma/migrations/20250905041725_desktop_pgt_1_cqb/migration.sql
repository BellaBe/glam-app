-- DropIndex
DROP INDEX "notifications_provider_message_id_key";

-- CreateIndex
CREATE INDEX "notifications_provider_message_id_idx" ON "notifications"("provider_message_id");
