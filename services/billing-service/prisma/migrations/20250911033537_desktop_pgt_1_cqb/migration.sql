/*
  Warnings:

  - You are about to drop the column `trial_ends_at` on the `billing_records` table. All the data in the column will be lost.

*/
-- DropIndex
DROP INDEX "billing_records_trial_ends_at_idx";

-- AlterTable
ALTER TABLE "billing_records" DROP COLUMN "trial_ends_at",
ADD COLUMN     "plarform_name" TEXT,
ADD COLUMN     "platform_shop_id" TEXT;
