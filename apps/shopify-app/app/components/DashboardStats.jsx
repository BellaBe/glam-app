import { Grid, Card, Text, BlockStack, InlineStack, Badge, Icon } from "@shopify/polaris";
import { CameraIcon, CreditCardIcon, ProductIcon } from "@shopify/polaris-icons";

export default function DashboardStats({
  selfiesToday,
  creditsRemaining,
  creditsLimit,
  syncStatus,
  productCount,
}) {
  const stats = [
    {
      title: "Selfies Today",
      value: selfiesToday.toLocaleString(),
      icon: CameraIcon,
      tone: "base",
    },
    {
      title: "Credits Remaining",
      value: `${creditsRemaining.toLocaleString()} / ${creditsLimit.toLocaleString()}`,
      icon: CreditCardIcon,
      tone: creditsRemaining < creditsLimit * 0.1 ? "critical" : "success",
    },
    {
      title: "Catalog Status",
      value: productCount > 0 ? `${productCount} products` : "Not synced",
      icon: ProductIcon,
      tone: syncStatus === "error" ? "critical" : productCount > 0 ? "success" : "warning",
    },
  ];

  return (
    <Grid>
      {stats.map((stat, index) => (
        <Grid.Cell key={index} columnSpan={{ xs: 6, sm: 6, md: 4, lg: 4, xl: 4 }}>
          <Card>
            <BlockStack gap="300">
              <InlineStack align="space-between">
                <Icon source={stat.icon} tone={stat.tone} />
                <Badge tone={stat.tone}>
                  {stat.tone === "success" ? "Good" : stat.tone === "critical" ? "Alert" : "Info"}
                </Badge>
              </InlineStack>
              <BlockStack gap="200">
                <Text tone="subdued" variant="bodyMd">
                  {stat.title}
                </Text>
                <Text variant="headingLg" as="p">
                  {stat.value}
                </Text>
              </BlockStack>
            </BlockStack>
          </Card>
        </Grid.Cell>
      ))}
    </Grid>
  );
}
