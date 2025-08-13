
// apps/shopify-bff/app/routes/webhooks.relay.jsx
import { authenticate } from "../shopify.server";
import apiClient from "../lib/apiClient";

export const action = async ({ request }) => {
  const { topic, shop, payload, webhookId } = await authenticate.webhook(request);

  console.log(`[Webhook Relay] ${topic} from ${shop}`);

  try {
    // Fire-and-forget webhook relay with proper headers
    void apiClient.relayShopifyWebhook({
      topic,
      shop,
      payload,
      webhookId,
    });

    console.log(`[Webhook Relay] Successfully relayed ${topic} webhook`);
  } catch (error) {
    console.error(`[Webhook Relay] Failed to relay ${topic} webhook:`, error.message);
    // Still return 200 to Shopify to avoid retries
  }

  return new Response(JSON.stringify({ 
    relayed: true,
    topic,
    shop: shop.replace(/\.myshopify\.com$/, '***') // Mask shop name in logs
  }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};