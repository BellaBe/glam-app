import { useLoaderData, useFetcher, useNavigate } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  Button,
  Text,
  Badge,
  CalloutCard,
  ProgressBar,
  BlockStack,
  InlineStack,
  Box,
} from "@shopify/polaris";
import { authenticate } from "../shopify.server";
import apiClient from "../lib/apiClient";
import { useState, useEffect } from "react";
import DashboardStats from "../components/DashboardStats";
import SubscriptionStatus from "../components/SubscriptionStatus";

export const loader = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const shop = session.shop;

  // Fetch data from external API
  const [merchantStatus, creditsStatus, catalogStatus, analytics] = await Promise.all([
    apiClient.getMerchant(shop),
    apiClient.getCreditsStatus(shop),
    apiClient.getCatalogStatus(shop),
    apiClient.getAnalytics(
      shop,
      new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      new Date().toISOString()
    ),
  ]);

  return Response.json({
    shop,
    subscription: merchantStatus.data || {
      status: "inactive",
      plan: null,
      trialEndsAt: null,
      nextBillingDate: null,
    },
    credits: creditsStatus.data || {
      used: 0,
      limit: 0,
      resetsAt: null,
    },
    catalog: catalogStatus.data || {
      productCount: 0,
      lastSyncAt: null,
      syncStatus: "idle",
    },
    analytics: analytics.data || {
      selfiesToday: 0,
      recommendationsToday: 0,
    },
  });
};

export const action = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const formData = await request.formData();
  const action = formData.get("action");

  if (action === "start_trial") {
    const result = await apiClient.startTrial(session.shop);
    return Response.json(result);
  }

  if (action === "sync_catalog") {
    const result = await apiClient.syncCatalog(session.shop);
    return Response(result);
  }

  return Response.json({ error: "Invalid action" });
};

export default function Index() {
  const { shop, subscription, credits, catalog, analytics } = useLoaderData();
  const fetcher = useFetcher();
  const navigate = useNavigate();
  const [syncProgress, setSyncProgress] = useState(null);

  // WebSocket for catalog sync progress
  useEffect(() => {
    if (fetcher.data?.websocket_url) {
      const ws = new WebSocket(fetcher.data.websocket_url);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "progress") {
          setSyncProgress({
            percent: (data.processed / data.total) * 100,
            message: data.message,
          });
        } else if (data.type === "complete") {
          setSyncProgress(null);
          ws.close();
          // Reload page to get updated data
          window.location.reload();
        }
      };

      ws.onerror = () => {
        setSyncProgress(null);
        ws.close();
      };

      return () => ws.close();
    }
  }, [fetcher.data]);

  const handleStartTrial = () => {
    fetcher.submit({ action: "start_trial" }, { method: "post" });
  };

  const handleSyncCatalog = () => {
    fetcher.submit({ action: "sync_catalog" }, { method: "post" });
  };

  const checklistItems = [
    {
      label: subscription.status === "inactive" ? "Start free trial" : "Subscription active",
      completed: subscription.status !== "inactive",
      action: subscription.status === "inactive" ? handleStartTrial : null,
    },
    {
      label: catalog.productCount > 0 ? `${catalog.productCount} products synced` : "Sync catalog",
      completed: catalog.productCount > 0,
      action: catalog.productCount === 0 ? handleSyncCatalog : null,
    },
    {
      label: "View analytics",
      completed: analytics.selfiesToday > 0 || analytics.recommendationsToday > 0,
      action: () => navigate("/app/analytics"),
    },
  ];

  return (
    <Page>
      <Layout>
        <Layout.Section>
          <SubscriptionStatus
            subscription={subscription}
            onStartTrial={handleStartTrial}
            onViewPlans={() => navigate("/app/billing")}
          />
        </Layout.Section>

        <Layout.Section>
          <DashboardStats
            selfiesToday={analytics.selfiesToday}
            creditsRemaining={credits.limit - credits.used}
            creditsLimit={credits.limit}
            syncStatus={catalog.syncStatus}
            productCount={catalog.productCount}
          />
        </Layout.Section>

        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <Text variant="headingMd" as="h2">
                Getting Started
              </Text>
              <ProgressBar
                size="small"
                progress={checklistItems.filter((item) => item.completed).length * 33.33}
              />
              <BlockStack gap="300">
                {checklistItems.map((item, index) => (
                  <InlineStack key={index} align="space-between" blockAlign="center">
                    <InlineStack gap="200" blockAlign="center">
                      <Box>
                        {item.completed ? <Badge tone="success">✓</Badge> : <Badge>Pending</Badge>}
                      </Box>
                      <Text>{item.label}</Text>
                    </InlineStack>
                    {item.action && !item.completed && (
                      <Button size="slim" onClick={item.action}>
                        Complete
                      </Button>
                    )}
                  </InlineStack>
                ))}
              </BlockStack>
            </BlockStack>
          </Card>
        </Layout.Section>

        {syncProgress && (
          <Layout.Section>
            <CalloutCard
              title="Syncing catalog..."
              illustration="https://cdn.shopify.com/s/files/1/0583/6465/7734/files/tag.svg?v=1701930959"
              primaryAction={{
                content: `${Math.round(syncProgress.percent)}% Complete`,
                disabled: true,
              }}
            >
              <Text>{syncProgress.message}</Text>
            </CalloutCard>
          </Layout.Section>
        )}
      </Layout>
    </Page>
  );
}

export function ErrorBoundary({ error }) {
  return (
    <Page>
      <Layout>
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Text variant="headingMd" as="h2">
                Something went wrong
              </Text>
              <Text tone="critical">{error.message}</Text>
              <Button url="/app" primary>
                Return to dashboard
              </Button>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}
