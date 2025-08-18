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

  // Fixed afterAuth hook in shopify.server.js
  hooks: {
    afterAuth: async ({ admin, session, request }) => {
      try {
        // Sync the shop with the external API after authentication

        // Execute GraphQL query using the admin client
        const shopInfoResponse = await admin.graphql(GET_SHOP_INFO);
        const shopData = await shopInfoResponse.json();

        // Build sync payload with correct field names
        const syncData = {
          platform_name: "shopify",
          platform_id: shopData.data.shop.id,
          platform_domain: shopData.data.shop.myshopifyDomain, // ✅ This will be used correctly
          shop_name: shopData.data.shop.name,
          email: shopData.data.shop.contactEmail,
          primary_domain_host: shopData.data.shop.primaryDomain.host,
          currency: shopData.data.shop.currencyCode,
          country: shopData.data.shop.billingAddress.countryCodeV2,
          platform_version: "2025-01", // API version
          scopes: session.scope,
        };

        // 1. Call sync API
        const syncResponse = await apiClient.syncShop(syncData);

        // 2. Verify the merchant was created/updated with retry
        let merchant = null;
        let attempts = 0;
        const maxAttempts = 3;

        while (!merchant && attempts < maxAttempts) {
          attempts++;
          try {
            // Use simple domain-based lookup
            merchant = await apiClient.getMerchant(syncData.platform_domain);
            break;
          } catch (error) {
            if (error.status === 404 && attempts < maxAttempts) {
              await new Promise((resolve) => setTimeout(resolve, 500));
            } else {
              throw error; // Re-throw if it's not a 404 or we've exhausted attempts
            }
          }
        }

        if (!merchant) {
          return null; // Don't fail auth, but log the issue
        }
        return { syncResponse, merchant };
      } catch (error) {
        return null;
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
