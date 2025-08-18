import {
  Card,
  Button,
  Banner,
  Text,
  BlockStack,
  InlineStack,
  Badge,
  ProgressBar,
} from "@shopify/polaris";

export default function CatalogSync({ lastSync, productCount, syncing, progress, onSync }) {
  const formatTimeAgo = (date) => {
    if (!date) return "Never";

    const seconds = Math.floor((new Date() - new Date(date)) / 1000);

    if (seconds < 60) return "Just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
  };

  return (
    <Card>
      <BlockStack gap="400">
        <InlineStack align="space-between">
          <Text variant="headingMd" as="h2">
            Catalog Sync
          </Text>
          {productCount > 0 && <Badge tone="success">{productCount} Products</Badge>}
        </InlineStack>

        {lastSync && (
          <InlineStack gap="200">
            <Text tone="subdued">Last synced:</Text>
            <Text>{formatTimeAgo(lastSync)}</Text>
          </InlineStack>
        )}

        {syncing ? (
          <BlockStack gap="300">
            <ProgressBar progress={progress?.percent || 0} />
            <Text>{progress?.message || "Starting sync..."}</Text>
            {progress?.processed && (
              <Text tone="subdued">
                {progress.processed} / {progress.total} products processed
              </Text>
            )}
          </BlockStack>
        ) : (
          <InlineStack gap="200">
            <Button primary onClick={onSync}>
              Sync Products Now
            </Button>
            {productCount > 0 && <Button plain>View sync settings</Button>}
          </InlineStack>
        )}

        {productCount === 0 && !syncing && (
          <Banner tone="warning">
            <Text>No products synced yet. Sync your catalog to enable selfie recommendations.</Text>
          </Banner>
        )}
      </BlockStack>
    </Card>
  );
}
