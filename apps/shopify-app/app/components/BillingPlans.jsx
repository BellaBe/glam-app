import { Grid, Card, Text, Button, BlockStack, InlineStack, Badge, List } from "@shopify/polaris";

export default function BillingPlans({ currentPlan, onSelectPlan, loading }) {
  const plans = [
    {
      id: "starter",
      name: "Starter",
      price: 29,
      credits: "1,000",
      features: ["Basic analytics", "Email support", "Manual catalog sync"],
      recommended: false,
    },
    {
      id: "growth",
      name: "Growth",
      price: 99,
      credits: "5,000",
      features: ["Advanced analytics", "Priority support", "Auto-sync daily", "Export data"],
      recommended: true,
    },
    {
      id: "enterprise",
      name: "Enterprise",
      price: 299,
      credits: "Unlimited",
      features: ["Real-time sync", "Dedicated support", "API access", "Custom reports"],
      recommended: false,
    },
  ];

  return (
    <BlockStack gap="400">
      <Text variant="headingMd" as="h2">
        Choose Your Plan
      </Text>
      <Grid>
        {plans.map((plan) => (
          <Grid.Cell key={plan.id} columnSpan={{ xs: 6, sm: 6, md: 4, lg: 4, xl: 4 }}>
            <Card>
              <BlockStack gap="400">
                {plan.recommended && <Badge tone="success">Recommended</Badge>}
                <BlockStack gap="200">
                  <Text variant="headingLg" as="h3">
                    {plan.name}
                  </Text>
                  <InlineStack gap="100" blockAlign="baseline">
                    <Text variant="heading2xl" as="p">
                      ${plan.price}
                    </Text>
                    <Text tone="subdued">/month</Text>
                  </InlineStack>
                  <Text tone="subdued">{plan.credits} credits/month</Text>
                </BlockStack>
                <List>
                  {plan.features.map((feature, index) => (
                    <List.Item key={index}>{feature}</List.Item>
                  ))}
                </List>
                <Button
                  fullWidth
                  primary={plan.recommended}
                  disabled={currentPlan === plan.id || loading}
                  loading={loading}
                  onClick={() => onSelectPlan(plan.id)}
                >
                  {currentPlan === plan.id ? "Current Plan" : `Choose ${plan.name}`}
                </Button>
              </BlockStack>
            </Card>
          </Grid.Cell>
        ))}
      </Grid>
    </BlockStack>
  );
}
