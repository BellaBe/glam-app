/*
  Warnings:

  - You are about to drop the column `platform_id` on the `merchants` table. All the data in the column will be lost.
  - A unique constraint covering the columns `[platform_name,platform_shop_id]` on the table `merchants` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `platform_shop_id` to the `merchants` table without a default value. This is not possible if the table is not empty.
  - Made the column `country` on table `merchants` required. This step will fail if there are existing NULL values in that column.
  - Made the column `scopes` on table `merchants` required. This step will fail if there are existing NULL values in that column.

*/
-- DropIndex
DROP INDEX "merchants_platform_id_domain_idx";

-- DropIndex
DROP INDEX "merchants_platform_name_platform_id_key";

-- AlterTable
ALTER TABLE "merchants" DROP COLUMN "platform_id",
ADD COLUMN     "platform_shop_id" TEXT NOT NULL,
ALTER COLUMN "currency" DROP DEFAULT,
ALTER COLUMN "country" SET NOT NULL,
ALTER COLUMN "platform_version" DROP NOT NULL,
ALTER COLUMN "scopes" SET NOT NULL;

-- CreateIndex
CREATE INDEX "merchants_platform_shop_id_domain_idx" ON "merchants"("platform_shop_id", "domain");

-- CreateIndex
CREATE UNIQUE INDEX "merchants_platform_name_platform_shop_id_key" ON "merchants"("platform_name", "platform_shop_id");
