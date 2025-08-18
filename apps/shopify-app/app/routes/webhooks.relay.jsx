// apps/shopify-bff/app/routes/webhooks.relay.jsx
import { authenticate } from "../shopify.server";
import apiClient from "../lib/apiClient";

export const action = async ({ request }) => {
  const { topic, shop, payload, webhookId } = await authenticate.webhook(request);

  try {
    // Fire-and-forget webhook relay with proper headers
    void apiClient.relayShopifyWebhook({
      topic,
      shop,
      payload,
      webhookId,
    });
  } catch (error) {
    // Still return 200 to Shopify to avoid retries
  }

  return new Response(
    JSON.stringify({
      relayed: true,
      topic,
      shop: shop.replace(/\.myshopify\.com$/, "***"), // Mask shop name in logs
    }),
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }
  );
};
