import "@shopify/shopify-app-remix/adapters/node";
import { ApiVersion, AppDistribution, shopifyApp } from "@shopify/shopify-app-remix/server";
import { PrismaSessionStorage } from "@shopify/shopify-app-session-storage-prisma";
import prisma from "./db.server";
import apiClient from "./lib/apiClient";
import { GET_SHOP_INFO } from "./query";
const shopify = shopifyApp({
  apiKey: process.env.SHOPIFY_API_KEY,
  apiSecretKey: process.env.SHOPIFY_API_SECRET || "",
  apiVersion: ApiVersion.January25,
  scopes: process.env.SCOPES?.split(","),
  appUrl: process.env.SHOPIFY_APP_URL || "",
  authPathPrefix: "/auth",
  sessionStorage: new PrismaSessionStorage(prisma),
  distribution: AppDistribution.AppStore,
  future: {
    unstable_newEmbeddedAuthStrategy: true,
    removeRest: true,
  },
  ...(process.env.SHOP_CUSTOM_DOMAIN
    ? { customShopDomains: [process.env.SHOP_CUSTOM_DOMAIN] }
    : {}),

  hooks: {
    afterAuth: async ({ admin, session }) => {
      try {
        const shopInfoResponse = await admin.graphql(GET_SHOP_INFO);
        const shopData = await shopInfoResponse.json();

        const syncData = {
          platform_name: "shopify",
          platform_shop_id: shopData.data.shop.id,
          domain: shopData.data.shop.myshopifyDomain,
          shop_name: shopData.data.shop.name,
          email: shopData.data.shop.contactEmail,
          primary_domain_host: shopData.data.shop.primaryDomain.host,
          currency: shopData.data.shop.currencyCode,
          country: shopData.data.shop.billingAddress.countryCodeV2,
          platform_version: "2025-01",
          scopes: session.scope,
        };

        // Fire and forget: merchant service handles idempotency + emits events
        await apiClient.syncShop(syncData);
      } catch (err) {
        console.error("Merchant sync failed:", err);
      }
    },
  },
});

export default shopify;
export const apiVersion = ApiVersion.January25;
export const addDocumentResponseHeaders = shopify.addDocumentResponseHeaders;
export const authenticate = shopify.authenticate;
export const unauthenticated = shopify.unauthenticated;
export const login = shopify.login;
export const registerWebhooks = shopify.registerWebhooks;
export const sessionStorage = shopify.sessionStorage;
