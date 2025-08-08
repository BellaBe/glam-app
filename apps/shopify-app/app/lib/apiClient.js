const API_BASE_URL = process.env.GLAM_API_URL
const API_KEY = process.env.GLAM_API_KEY;

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.apiKey = API_KEY;
    this.api_version = 'api/v1';
    console.log("[API Client] Initialized with base URL:", this.baseURL, "and API key:", this.apiKey, "api version:", this.api_version);
    
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${this.api_version}${endpoint}`;

    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
        'X-Shop-Domain': options.shop || '',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || `API Error: ${response.status}`);
      }

      return {
        data: data.data || data,
        error: null,
        meta: data.meta || {},
        pagination: data.pagination || null,
        links: data.links || {}
      };
    } catch (error) {
      console.error(`API Request Failed: ${endpoint}`, error);
      return {
        data: null,
        error: {
          message: error.message,
          status: error.status || 500
        },
        meta: {},
        pagination: null,
        links: {}
      };
    }
  }
  
  async syncShop(shop) {
    return this.request('/merchants/sync', {
      method: 'POST',
      shop,
      body: JSON.stringify({ shop })
    });
  }

  // Merchant endpoints
  async startTrial(shop) {
    return this.request('/merchants/trial', {
      method: 'POST',
      shop,
      body: JSON.stringify({ shop })
    });
  }

  async createSubscription(shop, plan, chargeId) {
    return this.request('/merchants/subscription', {
      method: 'POST',
      shop,
      body: JSON.stringify({ shop, plan, charge_id: chargeId })
    });
  }

  async getMerchantStatus(shop) {
    return this.request(`/merchants/status?shop=${shop}`, {
      method: 'GET',
      shop
    });
  }

  // Catalog endpoints
  async syncCatalog(shop) {
    return this.request('/catalog/sync', {
      method: 'POST',
      shop,
      body: JSON.stringify({ shop })
    });
  }

  async getCatalogStatus(shop) {
    return this.request(`/catalog/status?shop=${shop}`, {
      method: 'GET',
      shop
    });
  }

  // Credits endpoints
  async getCreditsStatus(shop) {
    return this.request(`/api/credits/status?shop=${shop}`, {
      method: 'GET',
      shop
    });
  }

  // Analytics endpoints
  async getAnalytics(shop, from, to) {
    return this.request(`/api/analysis/overview?shop=${shop}&from=${from}&to=${to}`, {
      method: 'GET',
      shop
    });
  }
  // Add this method to the ApiClient class in apiClient.js

  // Support endpoints
  async submitSupportTicket(ticketData) {
    return this.request('/api/support/ticket', {
      method: 'POST',
      shop: ticketData.shop,
      body: JSON.stringify({
        subject: ticketData.subject,
        category: ticketData.category,
        priority: ticketData.priority,
        message: ticketData.message,
        email: ticketData.email,
        shop: ticketData.shop
      })
    });
  }

  async getSupportTickets(shop) {
    return this.request(`/api/support/tickets?shop=${shop}`, {
      method: 'GET',
      shop
    });
  }

  async getSystemStatus() {
    return this.request('/api/system/status', {
      method: 'GET'
    });
  }
}


export default new ApiClient();