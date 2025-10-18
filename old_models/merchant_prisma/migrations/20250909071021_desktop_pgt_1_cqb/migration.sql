-- AlterTable
ALTER TABLE "merchants" ALTER COLUMN "installed_at" DROP NOT NULL,
ALTER COLUMN "installed_at" DROP DEFAULT;
