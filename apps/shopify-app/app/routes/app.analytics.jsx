import { useLoaderData, useFetcher } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  Text,
  DatePicker,
  Select,
  Button,
  DataTable,
  BlockStack,
  InlineStack,
  Badge,
  Grid,
  Popover,
  Banner,
  SkeletonBodyText,
  SkeletonDisplayText,
} from "@shopify/polaris";
import { authenticate } from "../shopify.server";
import apiClient from "../lib/apiClient";
import { useState, useCallback } from "react";

export const loader = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const shop = session.shop;

  const url = new URL(request.url);
  const from =
    url.searchParams.get("from") || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
  const to = url.searchParams.get("to") || new Date().toISOString();

  const analytics = await apiClient.getAnalytics(shop, from, to);

  return Response.json({
    shop,
    analytics: analytics.data || {
      selfie_uploads: { total: 0, by_day: [] },
      recommendations: { total: 0, click_through_rate: 0, by_product: [] },
      conversion_metrics: {
        views: 0,
        clicks: 0,
        purchases: 0,
        return_rate_before: 0,
        return_rate_after: 0,
      },
    },
    dateRange: { from, to },
  });
};

export const action = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const formData = await request.formData();
  const action = formData.get("action");

  if (action === "export") {
    const from = formData.get("from");
    const to = formData.get("to");
    const format = formData.get("format");

    // In real implementation, this would trigger a download
    // For now, we'll just return success
    return Response.json({
      success: true,
      message: `Export initiated in ${format} format`,
    });
  }

  return Response.json({ error: "Invalid action" });
};

export default function Analytics() {
  const { shop, analytics, dateRange } = useLoaderData();
  const fetcher = useFetcher();
  const [selectedDateRange, setSelectedDateRange] = useState({
    start: new Date(dateRange.from),
    end: new Date(dateRange.to),
  });
  const [datePickerActive, setDatePickerActive] = useState(false);
  const [exportFormat, setExportFormat] = useState("csv");

  const handleDateChange = useCallback((value) => {
    setSelectedDateRange(value);
  }, []);

  const handleApplyDateRange = () => {
    window.location.href = `/app/analytics?from=${selectedDateRange.start.toISOString()}&to=${selectedDateRange.end.toISOString()}`;
  };

  const handleExport = () => {
    fetcher.submit(
      {
        action: "export",
        from: selectedDateRange.start.toISOString(),
        to: selectedDateRange.end.toISOString(),
        format: exportFormat,
      },
      { method: "post" }
    );
  };

  // Calculate key metrics
  const conversionRate =
    analytics.recommendations.total > 0
      ? (analytics.recommendations.click_through_rate * 100).toFixed(2)
      : "0.00";

  const returnRateReduction =
    analytics.conversion_metrics.return_rate_before > 0
      ? (
          ((analytics.conversion_metrics.return_rate_before -
            analytics.conversion_metrics.return_rate_after) /
            analytics.conversion_metrics.return_rate_before) *
          100
        ).toFixed(1)
      : "0.0";

  // Prepare chart data
  const chartData = analytics.selfie_uploads.by_day.map((day) => ({
    date: new Date(day.date).toLocaleDateString(),
    selfies: day.count,
    recommendations: day.recommendations || 0,
  }));

  // Top performing products table
  const topProductsRows = (analytics.recommendations.by_product || [])
    .slice(0, 10)
    .map((product) => [
      product.name,
      product.recommendations.toString(),
      product.clicks.toString(),
      `${((product.clicks / product.recommendations) * 100).toFixed(1)}%`,
      <Badge key={product.name} tone={product.conversion_rate > 0.3 ? "success" : "info"}>
        {(product.conversion_rate * 100).toFixed(1)}%
      </Badge>,
    ]);

  // Loading state
  if (fetcher.state === "loading") {
    return (
      <Page title="Analytics" breadcrumbs={[{ content: "Dashboard", url: "/app" }]}>
        <Layout>
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <SkeletonDisplayText size="small" />
                <SkeletonBodyText lines={3} />
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Page
      title="Analytics"
      breadcrumbs={[{ content: "Dashboard", url: "/app" }]}
      primaryAction={{
        content: "Export Data",
        onAction: handleExport,
      }}
    >
      <Layout>
        {fetcher.data?.success && (
          <Layout.Section>
            <Banner title="Export started" tone="success" onDismiss={() => {}}>
              <Text>{fetcher.data.message}</Text>
            </Banner>
          </Layout.Section>
        )}

        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <InlineStack align="space-between">
                <Text variant="headingMd" as="h2">
                  Date Range
                </Text>
                <Popover
                  active={datePickerActive}
                  activator={
                    <Button onClick={() => setDatePickerActive(!datePickerActive)}>
                      {selectedDateRange.start.toLocaleDateString()} -{" "}
                      {selectedDateRange.end.toLocaleDateString()}
                    </Button>
                  }
                  onClose={() => setDatePickerActive(false)}
                >
                  <Card>
                    <BlockStack gap="400">
                      <DatePicker
                        month={selectedDateRange.start.getMonth()}
                        year={selectedDateRange.start.getFullYear()}
                        onChange={handleDateChange}
                        selectedDates={selectedDateRange}
                        allowRange
                      />
                      <InlineStack gap="200">
                        <Button primary onClick={handleApplyDateRange}>
                          Apply
                        </Button>
                        <Button onClick={() => setDatePickerActive(false)}>Cancel</Button>
                      </InlineStack>
                    </BlockStack>
                  </Card>
                </Popover>
              </InlineStack>
            </BlockStack>
          </Card>
        </Layout.Section>

        <Layout.Section>
          <Grid>
            <Grid.Cell columnSpan={{ xs: 6, sm: 3, md: 3, lg: 3, xl: 3 }}>
              <Card>
                <BlockStack gap="200">
                  <Text tone="subdued">Total Selfies</Text>
                  <Text variant="heading2xl">
                    {analytics.selfie_uploads.total.toLocaleString()}
                  </Text>
                  <Badge tone="success">Active</Badge>
                </BlockStack>
              </Card>
            </Grid.Cell>
            <Grid.Cell columnSpan={{ xs: 6, sm: 3, md: 3, lg: 3, xl: 3 }}>
              <Card>
                <BlockStack gap="200">
                  <Text tone="subdued">Recommendations</Text>
                  <Text variant="heading2xl">
                    {analytics.recommendations.total.toLocaleString()}
                  </Text>
                  <Text tone="subdued">Generated</Text>
                </BlockStack>
              </Card>
            </Grid.Cell>
            <Grid.Cell columnSpan={{ xs: 6, sm: 3, md: 3, lg: 3, xl: 3 }}>
              <Card>
                <BlockStack gap="200">
                  <Text tone="subdued">Click Rate</Text>
                  <Text variant="heading2xl">{conversionRate}%</Text>
                  <Badge tone={parseFloat(conversionRate) > 30 ? "success" : "attention"}>
                    {parseFloat(conversionRate) > 30 ? "Good" : "Improve"}
                  </Badge>
                </BlockStack>
              </Card>
            </Grid.Cell>
            <Grid.Cell columnSpan={{ xs: 6, sm: 3, md: 3, lg: 3, xl: 3 }}>
              <Card>
                <BlockStack gap="200">
                  <Text tone="subdued">Return Rate ↓</Text>
                  <Text variant="heading2xl">{returnRateReduction}%</Text>
                  <Badge tone="success">Reduced</Badge>
                </BlockStack>
              </Card>
            </Grid.Cell>
          </Grid>
        </Layout.Section>

        {chartData.length > 0 && (
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <Text variant="headingMd" as="h2">
                  Usage Trends
                </Text>
                <BlockStack gap="200">
                  <Text tone="subdued">
                    Daily activity over selected period (last 7 days shown)
                  </Text>
                  <DataTable
                    columnContentTypes={["text", "numeric", "numeric"]}
                    headings={["Date", "Selfies", "Recommendations"]}
                    rows={chartData.slice(-7).map((d) => [d.date, d.selfies, d.recommendations])}
                  />
                </BlockStack>
              </BlockStack>
            </Card>
          </Layout.Section>
        )}

        {topProductsRows.length > 0 && (
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <InlineStack align="space-between">
                  <Text variant="headingMd" as="h2">
                    Top Performing Products
                  </Text>
                  <Button plain>View all products</Button>
                </InlineStack>
                <DataTable
                  columnContentTypes={["text", "numeric", "numeric", "numeric", "text"]}
                  headings={["Product", "Recommendations", "Clicks", "CTR", "Conversion"]}
                  rows={topProductsRows}
                />
              </BlockStack>
            </Card>
          </Layout.Section>
        )}

        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <Text variant="headingMd" as="h2">
                Export Analytics
              </Text>
              <InlineStack gap="300">
                <Select
                  label="Format"
                  options={[
                    { label: "CSV", value: "csv" },
                    { label: "Excel", value: "xlsx" },
                    { label: "Response.json", value: "Response.json" },
                  ]}
                  value={exportFormat}
                  onChange={setExportFormat}
                />
                <Button primary onClick={handleExport} loading={fetcher.state === "submitting"}>
                  Export {exportFormat.toUpperCase()}
                </Button>
              </InlineStack>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}

export function ErrorBoundary({ error }) {
  return (
    <Page title="Analytics">
      <Layout>
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Text variant="headingMd" as="h2">
                Unable to load analytics
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
