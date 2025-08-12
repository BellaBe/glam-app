// apps/shopify-bff/app/routes/webhooks.relay.jsx
import { authenticate } from "../shopify.server";
import apiClient from "../lib/apiClient";

export const action = async ({ request }) => {
  const { topic, shop, payload, webhookId } = await authenticate.webhook(request);

  // Fire-and-forget (don’t await)
  void apiClient.relayShopifyWebhook({
    topic,
    shop,
    payload,
    webhookId,
  });

  return new Response(JSON.stringify({ relayed: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};
