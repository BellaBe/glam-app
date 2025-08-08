import type { ActionFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { authenticate } from "~/shopify.server";

/**
 * One endpoint handles every topic -> relays it to your BE server.
 */
export const action: ActionFunction = async ({ request }) => {
    
  const { topic, shop, payload } = await authenticate.webhook(request); // HMAC + header checks ✔️ :contentReference[oaicite:1]{index=1}

  // Fire-and-forget relay; don’t block Shopify’s 1-second handshake.
  fetch("https://west-block-shanghai-wma.trycloudflare.com/webhooks/shopify", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Topic": topic,
      "X-Shopify-Shop": shop,
    },
    body: JSON.stringify(payload),
  }).catch(console.error); // log but never throw—Shopify already got its 200.

  return json({ relayed: true });           // < 10 ms response
};
