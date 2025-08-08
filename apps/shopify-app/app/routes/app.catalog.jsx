import { json } from "@remix-run/node";
import { useLoaderData, useFetcher } from "@remix-run/react";
import { Page, Layout, Card, Button, Text, Badge, Banner, DataTable, BlockStack, InlineStack, ProgressBar, SkeletonBodyText } from "@shopify/polaris";
import { authenticate } from "../shopify.server";
import apiClient from "../lib/apiClient";
import { useState, useEffect } from "react";
import CatalogSync from "../components/CatalogSync";

export const loader = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const shop = session.shop;

  const catalogStatus = await apiClient.getCatalogStatus(shop);

  return json({
    shop,
    catalog: catalogStatus.data || {
      productCount: 0,
      lastSyncAt: null,
      syncHistory: [],
      syncStatus: 'idle'
    }
  });
};

export const action = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const formData = await request.formData();
  const action = formData.get("action");

  if (action === "sync") {
    const result = await apiClient.syncCatalog(session.shop);
    return json(result);
  }

  return json({ error: "Invalid action" });
};

export default function Catalog() {
  const { shop, catalog } = useLoaderData();
  const fetcher = useFetcher();
  const [syncing, setSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState(null);

  useEffect(() => {
    if (fetcher.data?.websocket_url) {
      setSyncing(true);
      const ws = new WebSocket(fetcher.data.websocket_url);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'progress') {
          setSyncProgress({
            percent: (data.processed / data.total) * 100,
            message: data.message,
            processed: data.processed,
            total: data.total
          });
        } else if (data.type === 'complete') {
          setSyncing(false);
          setSyncProgress(null);
          ws.close();
          window.location.reload();
        } else if (data.type === 'error') {
          setSyncing(false);
          setSyncProgress(null);
          ws.close();
        }
      };

      ws.onerror = () => {
        setSyncing(false);
        setSyncProgress(null);
        ws.close();
      };

      return () => ws.close();
    }
  }, [fetcher.data]);

  const handleSync = () => {
    fetcher.submit(
      { action: "sync" },
      { method: "post" }
    );
  };

  const syncHistoryRows = (catalog.syncHistory || []).map(sync => [
    new Date(sync.date).toLocaleString(),
    sync.productCount.toString(),
    `${sync.duration}s`,
    <Badge tone={sync.status === 'success' ? 'success' : sync.status === 'partial' ? 'warning' : 'critical'}>
      {sync.status}
    </Badge>
  ]);

  return (
    <Page
      title="Catalog Management"
      breadcrumbs={[{ content: 'Dashboard', url: '/app' }]}
      primaryAction={{
        content: 'View Products',
        url: `https://${shop}/admin/products`,
        external: true
      }}
    >
      <Layout>
        {catalog.syncStatus === 'error' && (
          <Layout.Section>
            <Banner
              title="Last sync failed"
              tone="critical"
              action={{
                content: 'Retry sync',
                onAction: handleSync
              }}
            >
              <Text>
                The previous catalog sync encountered an error. Please retry or contact support if the issue persists.
              </Text>
            </Banner>
          </Layout.Section>
        )}

        <Layout.Section>
          <CatalogSync
            lastSync={catalog.lastSyncAt}
            productCount={catalog.productCount}
            syncing={syncing}
            progress={syncProgress}
            onSync={handleSync}
          />
        </Layout.Section>

        {syncProgress && (
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <Text variant="headingMd" as="h2">Sync Progress</Text>
                <ProgressBar progress={syncProgress.percent} />
                <InlineStack align="space-between">
                  <Text>{syncProgress.message}</Text>
                  <Text tone="subdued">
                    {syncProgress.processed} / {syncProgress.total} products
                  </Text>
                </InlineStack>
              </BlockStack>
            </Card>
          </Layout.Section>
        )}

        {!syncing && catalog.productCount > 0 && (
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <InlineStack align="space-between">
                  <Text variant="headingMd" as="h2">Catalog Statistics</Text>
                  <Badge tone="success">{catalog.productCount} Products</Badge>
                </InlineStack>
                <BlockStack gap="200">
                  <InlineStack gap="400">
                    <Text tone="subdued">Last synced:</Text>
                    <Text>{catalog.lastSyncAt ? new Date(catalog.lastSyncAt).toLocaleString() : 'Never'}</Text>
                  </InlineStack>
                  <InlineStack gap="400">
                    <Text tone="subdued">Sync status:</Text>
                    <Badge tone={catalog.syncStatus === 'idle' ? 'info' : 'success'}>
                      {catalog.syncStatus}
                    </Badge>
                  </InlineStack>
                </BlockStack>
              </BlockStack>
            </Card>
          </Layout.Section>
        )}

        {syncHistoryRows.length > 0 && (
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <Text variant="headingMd" as="h2">Sync History</Text>
                <DataTable
                  columnContentTypes={['text', 'numeric', 'text', 'text']}
                  headings={['Date', 'Products', 'Duration', 'Status']}
                  rows={syncHistoryRows}
                />
              </BlockStack>
            </Card>
          </Layout.Section>
        )}
      </Layout>
    </Page>
  );
}