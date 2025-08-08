import { Card, Text, ProgressBar, Banner, BlockStack, InlineStack, Badge, Icon, Button } from "@shopify/polaris";
import { AlertCircleIcon } from "@shopify/polaris-icons";

export default function CreditUsage({ used, limit, resetsAt }) {
  const percentage = limit > 0 ? (used / limit) * 100 : 0;
  const remaining = limit - used;
  const isUnlimited = limit === -1 || limit === 0;
  
  const getDaysUntilReset = () => {
    if (!resetsAt) return null;
    const days = Math.ceil((new Date(resetsAt) - new Date()) / (1000 * 60 * 60 * 24));
    return days;
  };

  const getToneForUsage = () => {
    if (isUnlimited) return 'success';
    if (percentage >= 90) return 'critical';
    if (percentage >= 75) return 'warning';
    return 'success';
  };

  const tone = getToneForUsage();
  const daysUntilReset = getDaysUntilReset();

  return (
    <Card>
      <BlockStack gap="400">
        <InlineStack align="space-between">
          <Text variant="headingMd" as="h2">Credit Usage</Text>
          {!isUnlimited && percentage >= 75 && (
            <Badge tone={tone}>
              {percentage >= 90 ? 'Low Credits' : 'Monitor Usage'}
            </Badge>
          )}
        </InlineStack>

        {isUnlimited ? (
          <BlockStack gap="300">
            <InlineStack gap="200" blockAlign="center">
              <Badge tone="success">Unlimited Credits</Badge>
              <Text>Enterprise Plan</Text>
            </InlineStack>
            <Text tone="subdued">
              Your plan includes unlimited credits for selfie processing.
            </Text>
          </BlockStack>
        ) : (
          <BlockStack gap="300">
            <BlockStack gap="200">
              <InlineStack align="space-between">
                <Text variant="headingLg">
                  {used.toLocaleString()} / {limit.toLocaleString()}
                </Text>
                <Text tone="subdued">
                  {remaining.toLocaleString()} remaining
                </Text>
              </InlineStack>
              <ProgressBar 
                progress={percentage} 
                tone={tone}
                size="small"
              />
            </BlockStack>

            <InlineStack align="space-between">
              <Text tone="subdued">
                {Math.round(percentage)}% used this period
              </Text>
              {daysUntilReset && (
                <Text tone="subdued">
                  Resets in {daysUntilReset} {daysUntilReset === 1 ? 'day' : 'days'}
                </Text>
              )}
            </InlineStack>

            {percentage >= 90 && (
              <InlineStack gap="200" blockAlign="center">
                <Icon source={AlertCircleIcon} tone="critical" />
                <Text tone="critical">
                  You're running low on credits. Consider upgrading your plan.
                </Text>
              </InlineStack>
            )}

            {percentage >= 100 && (
              <BlockStack gap="200">
                <Banner tone="critical">
                  <Text>
                    Credit limit reached. New selfie requests will be blocked until your credits reset
                    {daysUntilReset && ` in ${daysUntilReset} days`}.
                  </Text>
                </Banner>
                <Button primary url="/app/billing">
                  Upgrade Plan
                </Button>
              </BlockStack>
            )}
          </BlockStack>
        )}

        <BlockStack gap="200">
          <Text variant="headingSm" tone="subdued">Credit Usage Breakdown</Text>
          <BlockStack gap="100">
            <InlineStack align="space-between">
              <Text tone="subdued">Selfie processing</Text>
              <Text>{Math.round(used * 0.7).toLocaleString()} credits</Text>
            </InlineStack>
            <InlineStack align="space-between">
              <Text tone="subdued">Recommendations generated</Text>
              <Text>{Math.round(used * 0.3).toLocaleString()} credits</Text>
            </InlineStack>
          </BlockStack>
        </BlockStack>

        {!isUnlimited && (
          <InlineStack gap="200">
            <Button plain>View detailed usage</Button>
            {percentage >= 75 && (
              <Button plain>Set up usage alerts</Button>
            )}
          </InlineStack>
        )}
      </BlockStack>
    </Card>
  );
}