import { json } from "@remix-run/node";
import { useLoaderData, useFetcher } from "@remix-run/react";
import { Page, Layout, Card, Text, Button, Banner, ProgressBar, Grid, BlockStack, InlineStack, Badge, DataTable } from "@shopify/polaris";
import { authenticate } from "../shopify.server";
import apiClient from "../lib/apiClient";
import BillingPlans from "../components/BillingPlans";
import CreditUsage from "../components/CreditUsage";

export const loader = async ({ request }) => {
  const { session, billing } = await authenticate.admin(request);
  const shop = session.shop;

  const [merchantStatus, creditsStatus] = await Promise.all([
    apiClient.getMerchantStatus(shop),
    apiClient.getCreditsStatus(shop)
  ]);

  return json({
    shop,
    subscription: merchantStatus.data,
    credits: creditsStatus.data,
    billing
  });
};

export const action = async ({ request }) => {
  const { session, billing } = await authenticate.admin(request);
  const formData = await request.formData();
  const plan = formData.get("plan");

  // Create Shopify recurring charge
  const planDetails = {
    starter: { price: 29, credits: 1000 },
    growth: { price: 99, credits: 5000 },
    enterprise: { price: 299, credits: -1 } // -1 for unlimited
  };

  const selectedPlan = planDetails[plan];
  if (!selectedPlan) {
    return json({ error: "Invalid plan selected" });
  }

  try {
    const charge = await billing.require({
      plan: plan,
      amount: selectedPlan.price,
      currencyCode: "USD",
      interval: "EVERY_30_DAYS"
    });

    // Notify external API about subscription
    const result = await apiClient.createSubscription(
      session.shop,
      plan,
      charge.id
    );

    return json(result);
  } catch (error) {
    return json({ error: error.message });
  }
};

export default function Billing() {
  const { shop, subscription, credits } = useLoaderData();
  const fetcher = useFetcher();

  const handleSelectPlan = (plan) => {
    fetcher.submit(
      { plan },
      { method: "post" }
    );
  };

  const billingHistory = [
    {
      date: '2024-01-15',
      amount: '$99.00',
      status: 'Paid',
      invoice: '#INV-001'
    },
    {
      date: '2023-12-15',
      amount: '$99.00',
      status: 'Paid',
      invoice: '#INV-002'
    }
  ];

  const rows = billingHistory.map(item => [
    item.date,
    item.amount,
    <Badge tone={item.status === 'Paid' ? 'success' : 'warning'}>{item.status}</Badge>,
    item.invoice
  ]);

  return (
    <Page
      title="Billing & Plans"
      breadcrumbs={[{ content: 'Dashboard', url: '/app' }]}
    >
      <Layout>
        {subscription?.status === 'trial' && (
          <Layout.Section>
            <Banner
              title="Free trial active"
              tone="info"
              action={{
                content: 'View plans',
                onAction: () => document.querySelector('#plans-section').scrollIntoView()
              }}
            >
              <Text>
                Your trial ends on {new Date(subscription.trialEndsAt).toLocaleDateString()}.
                Choose a plan to continue using Glam You Up after your trial.
              </Text>
            </Banner>
          </Layout.Section>
        )}

        {subscription?.plan && (
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <InlineStack align="space-between">
                  <BlockStack gap="200">
                    <Text variant="headingMd" as="h2">Current Plan</Text>
                    <InlineStack gap="200">
                      <Badge tone="success">{subscription.plan.toUpperCase()}</Badge>
                      <Text tone="subdued">
                        Next billing: {new Date(subscription.nextBillingDate).toLocaleDateString()}
                      </Text>
                    </InlineStack>
                  </BlockStack>
                  <Button plain>Change plan</Button>
                </InlineStack>
              </BlockStack>
            </Card>
          </Layout.Section>
        )}

        <Layout.Section>
          <CreditUsage
            used={credits?.used || 0}
            limit={credits?.limit || 0}
            resetsAt={credits?.resetsAt}
          />
        </Layout.Section>

        <Layout.Section id="plans-section">
          <BillingPlans
            currentPlan={subscription?.plan}
            onSelectPlan={handleSelectPlan}
            loading={fetcher.state === 'submitting'}
          />
        </Layout.Section>

        {billingHistory.length > 0 && (
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <Text variant="headingMd" as="h2">Billing History</Text>
                <DataTable
                  columnContentTypes={['text', 'text', 'text', 'text']}
                  headings={['Date', 'Amount', 'Status', 'Invoice']}
                  rows={rows}
                />
              </BlockStack>
            </Card>
          </Layout.Section>
        )}
      </Layout>
    </Page>
  );
}