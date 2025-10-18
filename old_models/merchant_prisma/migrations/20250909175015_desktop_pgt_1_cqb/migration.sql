/*
  Warnings:

  - You are about to drop the column `last_sync_at` on the `merchants` table. All the data in the column will be lost.
  - You are about to drop the column `status_changed_at` on the `merchants` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "merchants" DROP COLUMN "last_sync_at",
DROP COLUMN "status_changed_at",
ADD COLUMN     "last_synced_at" TIMESTAMPTZ(3),
ALTER COLUMN "installed_at" SET DATA TYPE TIMESTAMPTZ(3),
ALTER COLUMN "uninstalled_at" SET DATA TYPE TIMESTAMPTZ(3);

-- CreateIndex
CREATE INDEX "merchants_last_synced_at_idx" ON "merchants"("last_synced_at");
