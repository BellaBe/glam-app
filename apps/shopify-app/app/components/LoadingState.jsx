import {
  Card,
  SkeletonBodyText,
  SkeletonDisplayText,
  BlockStack,
  Layout,
  SkeletonThumbnail,
  InlineStack,
} from "@shopify/polaris";

export function LoadingState({ type = "page" }) {
  if (type === "card") {
    return (
      <Card>
        <BlockStack gap="400">
          <SkeletonDisplayText size="small" />
          <SkeletonBodyText lines={3} />
        </BlockStack>
      </Card>
    );
  }

  if (type === "table") {
    return (
      <Card>
        <BlockStack gap="400">
          <SkeletonDisplayText size="small" />
          <BlockStack gap="200">
            {[...Array(5)].map((_, i) => (
              <InlineStack key={i} gap="400" align="space-between">
                <SkeletonBodyText lines={1} />
                <SkeletonBodyText lines={1} />
                <SkeletonBodyText lines={1} />
                <SkeletonBodyText lines={1} />
              </InlineStack>
            ))}
          </BlockStack>
        </BlockStack>
      </Card>
    );
  }

  if (type === "stats") {
    return (
      <InlineStack gap="400">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <BlockStack gap="300">
              <SkeletonThumbnail size="small" />
              <SkeletonDisplayText size="small" />
              <SkeletonBodyText lines={1} />
            </BlockStack>
          </Card>
        ))}
      </InlineStack>
    );
  }

  // Default: full page loading
  return (
    <Layout>
      <Layout.Section>
        <Card>
          <BlockStack gap="400">
            <SkeletonDisplayText size="medium" />
            <SkeletonBodyText lines={2} />
          </BlockStack>
        </Card>
      </Layout.Section>
      <Layout.Section>
        <Card>
          <BlockStack gap="400">
            <SkeletonDisplayText size="small" />
            <SkeletonBodyText lines={4} />
          </BlockStack>
        </Card>
      </Layout.Section>
      <Layout.Section>
        <Card>
          <BlockStack gap="400">
            <SkeletonDisplayText size="small" />
            <SkeletonBodyText lines={3} />
          </BlockStack>
        </Card>
      </Layout.Section>
    </Layout>
  );
}

export function LoadingDashboard() {
  return (
    <Layout>
      <Layout.Section>
        <Card>
          <BlockStack gap="400">
            <InlineStack gap="400" align="space-between">
              <BlockStack gap="200">
                <SkeletonDisplayText size="medium" />
                <SkeletonBodyText lines={1} />
              </BlockStack>
              <SkeletonThumbnail size="medium" />
            </InlineStack>
          </BlockStack>
        </Card>
      </Layout.Section>
      <Layout.Section>
        <InlineStack gap="400">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <BlockStack gap="300">
                <InlineStack align="space-between">
                  <SkeletonThumbnail size="small" />
                  <SkeletonBodyText lines={1} />
                </InlineStack>
                <SkeletonBodyText lines={1} />
                <SkeletonDisplayText size="small" />
              </BlockStack>
            </Card>
          ))}
        </InlineStack>
      </Layout.Section>
      <Layout.Section>
        <Card>
          <BlockStack gap="400">
            <SkeletonDisplayText size="small" />
            <SkeletonBodyText lines={3} />
          </BlockStack>
        </Card>
      </Layout.Section>
    </Layout>
  );
}

export function LoadingInline() {
  return <SkeletonBodyText lines={1} />;
}

export default LoadingState;
