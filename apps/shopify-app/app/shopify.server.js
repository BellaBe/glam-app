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

  // Fixed afterAuth hook in shopify.server.js
  hooks: {
    afterAuth: async ({ admin, session, request }) => {
      console.log(`[SHOPIFY] After Auth: ${session.shop}`);

      try {
        // Sync the shop with the external API after authentication
        console.log("[SHOPIFY] Syncing shop after authentication...");

        // Execute GraphQL query using the admin client
        const shopInfoResponse = await admin.graphql(GET_SHOP_INFO);
        const shopData = await shopInfoResponse.json();

        console.log("[SHOPIFY] Shop data fetched successfully");

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

        console.log("[SHOPIFY] Sync payload prepared:", {
          shop: syncData.platform_domain,
          platform: syncData.platform,
          hasAccessToken: !!syncData.access_token,
        });

        // 1. Call sync API
        const syncResponse = await apiClient.syncShop(syncData);
        console.log("[SHOPIFY] Sync API returned:", syncResponse);

        // 2. Verify the merchant was created/updated with retry
        console.log("[SHOPIFY] Verifying merchant creation...");

        let merchant = null;
        let attempts = 0;
        const maxAttempts = 3;

        while (!merchant && attempts < maxAttempts) {
          attempts++;
          console.log(
            `[SHOPIFY] Verification attempt ${attempts}/${maxAttempts}`,
          );

          try {
            // Use simple domain-based lookup
            merchant = await apiClient.getMerchant(syncData.platform_domain);
            console.log("[SHOPIFY] Merchant verified successfully!");
            break;
          } catch (error) {
            if (error.status === 404 && attempts < maxAttempts) {
              console.log(`[SHOPIFY] Merchant not found yet, waiting 500ms...`);
              await new Promise((resolve) => setTimeout(resolve, 500));
            } else {
              throw error; // Re-throw if it's not a 404 or we've exhausted attempts
            }
          }
        }

        if (!merchant) {
          console.error("[SHOPIFY] Failed to verify merchant after sync");
          return null; // Don't fail auth, but log the issue
        }

        console.log(
          "[SHOPIFY] Shop sync and verification completed successfully!",
        );
        return { syncResponse, merchant };
      } catch (error) {
        // Handle fetch-style errors properly
        console.error("[SHOPIFY] ===== SYNC ERROR DETAILS =====");
        console.error("[SHOPIFY] Error message:", error.message);

        if (error.status) {
          // This is an API error with structured data
          console.error("[SHOPIFY] HTTP Status:", error.status);
          console.error("[SHOPIFY] Request URL:", error.url);
          console.error("[SHOPIFY] Request Method:", error.method);
          console.error(
            "[SHOPIFY] Response Data:",
            JSON.stringify(error.responseData, null, 2),
          );
          console.error(
            "[SHOPIFY] Request Headers:",
            JSON.stringify(error.requestHeaders, null, 2),
          );

          if (error.requestBody) {
            console.error(
              "[SHOPIFY] Request Body:",
              JSON.stringify(error.requestBody, null, 2),
            );
          }
        } else {
          // This is a network/parsing error
          console.error("[SHOPIFY] Error type: Network/Parsing error");
          console.error("[SHOPIFY] Full error:", error);
        }

        // Don't rethrow - log the error but allow auth to continue
        console.error("[SHOPIFY] Shop sync failed, but auth will continue");
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
