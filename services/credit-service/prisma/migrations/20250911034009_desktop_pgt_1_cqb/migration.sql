/*
  Warnings:

  - You are about to drop the column `platform_id` on the `credit_accounts` table. All the data in the column will be lost.
  - Added the required column `platform_shop_id` to the `credit_accounts` table without a default value. This is not possible if the table is not empty.

*/
-- DropIndex
DROP INDEX "credit_accounts_platform_name_platform_id_idx";

-- AlterTable
ALTER TABLE "credit_accounts" DROP COLUMN "platform_id",
ADD COLUMN     "platform_shop_id" TEXT NOT NULL;

-- CreateIndex
CREATE INDEX "credit_accounts_platform_name_platform_shop_id_idx" ON "credit_accounts"("platform_name", "platform_shop_id");
