import "@shopify/shopify-app-remix/adapters/node";
import {
  ApiVersion,
  AppDistribution,
  shopifyApp,
} from "@shopify/shopify-app-remix/server";
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
    afterAuth: async ({ admin, session, request }) => {
      console.log("[SHOPIFY] After Auth:", session);

      try {
        // Sync the shop with the external API after authentication
        console.log("[SHOPIFY] Syncing shop after authentication...");

        // Execute GraphQL query using the admin client
        const shopInfoResponse = await admin.graphql(GET_SHOP_INFO);
        const shopData = await shopInfoResponse.json();

        const syncData = {
          platform_name: "shopify",
          platform_id: shopData.data.shop.id,
          shop_name: shopData.data.shop.name,
          shop_url: shopData.data.shop.url,
          email: shopData.data.shop.email,
          contact_email: shopData.data.shop.contactEmail,
          currency_code: shopData.data.shop.currencyCode,
          primary_domain_url: shopData.data.shop.primaryDomain?.url,
          primary_domain_host: shopData.data.shop.primaryDomain?.host,
          myshopify_domain: shopData.data.shop.myshopifyDomain,
          platform_plan: shopData.data.shop.plan?.displayName,
          billing_address: JSON.stringify(shopData.data.shop.billingAddress),
        };

        // ADD THESE LOGS:
        console.log("[SHOPIFY] ===== SYNC REQUEST DEBUG =====");
        console.log("[SHOPIFY] Sync Data:", JSON.stringify(syncData, null, 2));
        console.log(
          "[SHOPIFY] Data Types:",
          Object.entries(syncData).map(
            ([k, v]) =>
              `${k}: ${typeof v} (${v === null ? "null" : v === undefined ? "undefined" : "valued"})`,
          ),
        );

        // Log what apiClient.syncShop actually sends
        console.log(
          "[SHOPIFY] API Client method being called:",
          apiClient.syncShop.toString(),
        );

        const syncResponse = await apiClient.syncShop(syncData);
        console.log("[SHOPIFY] Sync Shop Response:", syncResponse);
        if (syncResponse.error) {
          console.error("[SHOPIFY] Sync Shop Error:", syncResponse.error);
        } else {
          console.log("[SHOPIFY] Shop synced successfully:", syncResponse.data);
        }
      } catch (error) {
        console.error("[SHOPIFY] ===== SYNC ERROR DETAILS =====");
    console.error("[SHOPIFY] Status:", error.response?.status);
    console.error("[SHOPIFY] Response Data:", JSON.stringify(error.response?.data, null, 2));
    console.error("[SHOPIFY] Response Headers:", error.response?.headers);
    console.error("[SHOPIFY] Request Config:", {
        url: error.config?.url,
        method: error.config?.method,
        headers: error.config?.headers,
        data: error.config?.data
    });
    throw error;
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
