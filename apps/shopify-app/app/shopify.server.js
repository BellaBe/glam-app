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

        console.log("[SHOPIFY] Shop DATA:========", JSON.stringify(shopData, null, 2));

        const syncData = {
          shop_gid: shopData.data.shop.id,
          name: shopData.data.shop.name,
          url: shopData.data.shop.url,
          email: shopData.data.shop.email,
          currencyCode: shopData.data.shop.currencyCode,   
          primaryDomainDomain: shopData.data.shop.primaryDomain?.domain,
          primaryDomainHost: shopData.data.shop.primaryDomain?.host,
          plan: shopData.data.shop.plan?.displayName,
          myshopifyDomain: shopData.data.shop.myshopifyDomain,
          contactEmail: shopData.data.shop.contactEmail,
          country: shopData.data.shop.billingAddress?.countryCodeV2,
          accessToken: session.accessToken,
          scope: session.scope,
        };

        
        const syncResponse = await apiClient.syncShop(syncData);
        console.log("[SHOPIFY] Sync Shop Response:", syncResponse);
        if (syncResponse.error) {
          console.error("[SHOPIFY] Sync Shop Error:", syncResponse.error);
        } else {
          console.log("[SHOPIFY] Shop synced successfully:", syncResponse.data);
        }
      } catch (error) {
        console.error("[SHOPIFY] Error in afterAuth hook:", error);
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
