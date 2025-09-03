// apps/shopify-bff/app/lib/apiClient.js
import jwt from "jsonwebtoken";

// === 1. Add correlation ID generator ===
function generateCorrelationId() {
  return `corr_${Math.random().toString(16).slice(2, 14)}`;
}

const svc = {
  merchant: process.env.MERCHANT_URL,
  catalog: process.env.CATALOG_URL,
  credits: process.env.CREDITS_URL,
  analytics: process.env.ANALYTICS_URL,
  webhook: process.env.WEBHOOK_URL,
  billing: process.env.BILLING_URL,
};

function signJwt(shop) {
  const token = jwt.sign(
    {
      sub: shop,
      scope: "bff:api:access",
      iat: Math.floor(Date.now() / 1000),
      platform: "shopify",
    },
    process.env.CLIENT_JWT_SECRET,
    {
      expiresIn: process.env.JWT_ACCESS_TOKEN_EXPIRE_SECONDS,
      algorithm: process.env.JWT_ALGORITHM || "HS256",
    }
  );
  if (!token) throw new Error("Failed to create client JWT");
  return token;
}

// === 2. Add correlation header to API headers ===
function addApiHeaders(shop) {
  const token = signJwt(shop);

  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    "X-Shop-Platform": "shopify",
    "X-Shop-Domain": shop,
    "X-Correlation-ID": generateCorrelationId(),
  };
}

// === 3. Same for webhook headers ===
function addWebhookHeaders(shop, { webhookId = null, topic = null } = {}) {
  const token = signJwt(shop);

  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    "X-Shop-Platform": "shopify",
    "X-Shop-Domain": shop,
    "X-Webhook-Platform": "shopify",
    "X-Correlation-ID": generateCorrelationId(),
  };

  if (topic) {
    headers["X-Webhook-Topic"] = topic;
  }

  if (webhookId) {
    headers["X-Webhook-Id"] = webhookId;
    headers["X-Shopify-Webhook-Id"] = webhookId; // backward compatibility
  }

  return headers;
}

function buildUrl(base, path) {
  if (!base) throw new Error("API base URL not set");
  const baseNorm = base.endsWith("/") ? base : base + "/";
  const pathNorm = path.startsWith("/") ? path : "/" + path;
  return `${baseNorm}api/v1${pathNorm}`;
}

async function callAndForget(base, path, { method = "GET", shop, body, webhookId, topic } = {}) {
  const url = buildUrl(base, path);
  const headers = addWebhookHeaders(shop, { webhookId, topic });
  const controller = new AbortController();
  setTimeout(() => controller.abort(), 1500);

  fetch(url, {
    method,
    signal: controller.signal,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  }).catch((e) => console.error(`[API call ${method} ${url}] failed:`, e?.message || e));
}

async function call(base, path, { method = "GET", shop, body } = {}) {
  const url = buildUrl(base, path);
  const res = await fetch(url, {
    method,
    headers: addApiHeaders(shop),
    body: body ? JSON.stringify(body) : undefined,
  });

  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    const errorMsg = json?.error?.message || json?.detail?.message || `API ${res.status}`;
    throw new Error(errorMsg);
  }

  return json?.data ?? json;
}

export default {
  syncShop: (payload) =>
    call(svc.merchant, "/merchants/sync", {
      method: "POST",
      shop: payload.domain,
      body: payload,
    }),
  getMerchant: (shop) => call(svc.merchant, "/merchants/self", { shop }),

  startTrial: (shop) =>
    call(svc.merchant, "/billing/trial", {
      method: "POST",
      shop,
      body: { shop },
    }),

  createSubscription: (shop, plan, id) =>
    call(svc.billing, "/billing/subscription", {
      method: "POST",
      shop,
      body: { shop, plan, charge_id: id },
    }),

  syncCatalog: (shop) =>
    call(svc.catalog, "/catalog/sync", {
      method: "POST",
      shop,
      body: { shop },
    }),

  getCatalogStatus: (shop) => call(svc.catalog, `/catalog/status?shop=${shop}`, { shop }),

  getCreditsStatus: (shop) => call(svc.credits, `/credits/status?shop=${shop}`, { shop }),

  getAnalytics: (shop, from, to) =>
    call(svc.analytics, `/analysis/overview?shop=${shop}&from=${from}&to=${to}`, { shop }),

  relayShopifyWebhook: ({ topic, shop, payload, webhookId }) =>
    callAndForget(svc.webhook, "/webhooks/shopify", {
      method: "POST",
      shop,
      body: payload,
      webhookId,
      topic,
    }),
};
