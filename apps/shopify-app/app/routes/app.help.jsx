import { useLoaderData, useFetcher, useNavigate } from "@remix-run/react";
import { 
  Page, 
  Layout, 
  Card, 
  Text, 
  Button, 
  TextField, 
  Select, 
  BlockStack, 
  InlineStack, 
  Badge, 
  Banner,
  Link,
  List,
  Collapsible,
  Icon,
  CalloutCard,
  Grid,
  Box,
  Divider
} from "@shopify/polaris";
import { 
  BookOpenIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from "@shopify/polaris-icons";
import { authenticate } from "../shopify.server";
import apiClient from "../lib/apiClient";
import { useState, useCallback } from "react";
import { LoadingState } from "../components/LoadingState";

export const loader = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const shop = session.shop;

  // Fetch merchant status for context
  const merchantStatus = await apiClient.getMerchant(shop);

  return Response.json({
    shop,
    subscription: merchantStatus.data || { plan: null, status: 'inactive' },
    supportEmail: 'support@glamyouup.com',
    supportPhone: '1-800-GLAM-YOU'
  });
};

export const action = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const formData = await request.formData();
  const action = formData.get("action");

  if (action === "submit_ticket") {
    const ticketData = {
      shop: session.shop,
      subject: formData.get("subject"),
      category: formData.get("category"),
      priority: formData.get("priority"),
      message: formData.get("message"),
      email: formData.get("email")
    };

    // Submit to external API
    const result = await apiClient.submitSupportTicket(ticketData);
    return Response.Response.json(result);
  }

  return Response.Response.json({ error: "Invalid action" });
};

export default function Help() {
  const { shop, subscription, supportEmail, supportPhone } = useLoaderData();
  const fetcher = useFetcher();
  const navigate = useNavigate();

  // Form state
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('technical');
  const [priority, setPriority] = useState('normal');
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState({});

  // FAQ state
  const [expandedFaq, setExpandedFaq] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!subject.trim()) newErrors.subject = 'Subject is required';
    if (!message.trim()) newErrors.message = 'Message is required';
    if (!email.trim()) newErrors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Please enter a valid email';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      fetcher.submit(
        { 
          action: "submit_ticket",
          subject,
          category,
          priority,
          message,
          email
        },
        { method: "post" }
      );
    }
  };

  const toggleFaq = (id) => {
    setExpandedFaq(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const faqs = [
    {
      id: 'trial',
      question: 'How does the 14-day free trial work?',
      answer: 'Your free trial starts when you activate it and includes 500 credits to test our selfie-based recommendation system. No credit card required. You can upgrade to a paid plan anytime during or after the trial.'
    },
    {
      id: 'credits',
      question: 'What are credits and how are they used?',
      answer: 'Credits are consumed when processing selfies and generating recommendations. 1 selfie analysis = 1 credit. Credits reset monthly based on your billing cycle. Unused credits do not roll over.'
    },
    {
      id: 'sync',
      question: 'Why is my catalog sync failing?',
      answer: 'Common causes include: missing product images, products without published status, or temporary API issues. Ensure all products have images and are published. Try syncing again or contact support if the issue persists.'
    },
    {
      id: 'billing',
      question: 'How does billing work?',
      answer: 'We use Shopify\'s native billing system. Charges appear on your regular Shopify invoice. You can upgrade, downgrade, or cancel anytime. Changes take effect at the next billing cycle.'
    },
    {
      id: 'api',
      question: 'Can I integrate with my custom storefront?',
      answer: 'Yes! Enterprise plans include API access for custom integrations. You can use our REST API to process selfies and get recommendations programmatically.'
    },
    {
      id: 'accuracy',
      question: 'How accurate are the recommendations?',
      answer: 'Our AI achieves 92% accuracy in size recommendations and 87% in style matching. We continuously improve our models based on return data and user feedback.'
    },
    {
      id: 'privacy',
      question: 'How is customer data handled?',
      answer: 'We take privacy seriously. Selfies are processed in real-time and deleted immediately after analysis. We never store customer photos. All data is encrypted in transit and at rest.'
    },
    {
      id: 'returns',
      question: 'How much can this reduce returns?',
      answer: 'Merchants typically see 25-40% reduction in size-related returns. Results vary based on product category and implementation. Fashion apparel sees the highest improvement.'
    }
  ];

  const quickLinks = [
    {
      title: 'Getting Started Guide',
      description: 'Step-by-step setup instructions',
      url: 'https://docs.glamyouup.com/getting-started',
      icon: BookOpenIcon
    },
    {
      title: 'API Documentation',
      description: 'For developers and custom integrations',
      url: 'https://docs.glamyouup.com/api',
      icon: BookOpenIcon,
      requiresPlan: 'enterprise'
    },
    {
      title: 'Best Practices',
      description: 'Optimize your recommendation accuracy',
      url: 'https://docs.glamyouup.com/best-practices',
      icon: BookOpenIcon
    },
    {
      title: 'Video Tutorials',
      description: 'Visual guides for common tasks',
      url: 'https://glamyouup.com/tutorials',
      icon: BookOpenIcon
    }
  ];

  // Show success message if ticket was submitted
  const ticketSubmitted = fetcher.data?.data?.ticket_id;

  return (
    <Page
      title="Help & Support"
      breadcrumbs={[{ content: 'Dashboard', url: '/app' }]}
    >
      <Layout>
        {ticketSubmitted && (
          <Layout.Section>
            <Banner
              title="Support ticket submitted successfully"
              tone="success"
              onDismiss={() => window.location.reload()}
            >
              <Text>
                Your ticket #{fetcher.data.data.ticket_id} has been submitted. 
                We'll respond within 24 hours to {email}.
              </Text>
            </Banner>
          </Layout.Section>
        )}

        <Layout.Section>
          <Grid>
            <Grid.Cell columnSpan={{ xs: 6, sm: 6, md: 4, lg: 4, xl: 4 }}>
              <CalloutCard
                title="Email Support"
                illustration="https://cdn.shopify.com/s/files/1/0583/6465/7734/files/email.svg?v=1701930959"
                primaryAction={{
                  content: 'Send Email',
                  url: `mailto:${supportEmail}`,
                  external: true
                }}
              >
                <Text>{supportEmail}</Text>
                <Text tone="subdued">Response within 24 hours</Text>
              </CalloutCard>
            </Grid.Cell>

            <Grid.Cell columnSpan={{ xs: 6, sm: 6, md: 4, lg: 4, xl: 4 }}>
              <CalloutCard
                title="Priority Support"
                illustration="https://cdn.shopify.com/s/files/1/0583/6465/7734/files/phone.svg?v=1701930959"
                primaryAction={{
                  content: subscription?.plan === 'growth' || subscription?.plan === 'enterprise' 
                    ? 'Call Now' 
                    : 'Upgrade for Phone Support',
                  url: subscription?.plan === 'growth' || subscription?.plan === 'enterprise'
                    ? `tel:${supportPhone.replace(/-/g, '')}`
                    : '/app/billing',
                  external: subscription?.plan === 'growth' || subscription?.plan === 'enterprise'
                }}
              >
                <Text>{supportPhone}</Text>
                <Text tone="subdued">
                  {subscription?.plan === 'growth' || subscription?.plan === 'enterprise'
                    ? 'Mon-Fri 9am-6pm EST'
                    : 'Available on Growth & Enterprise'}
                </Text>
              </CalloutCard>
            </Grid.Cell>

            <Grid.Cell columnSpan={{ xs: 6, sm: 6, md: 4, lg: 4, xl: 4 }}>
              <CalloutCard
                title="Live Chat"
                illustration="https://cdn.shopify.com/s/files/1/0583/6465/7734/files/chat.svg?v=1701930959"
                primaryAction={{
                  content: subscription?.plan === 'enterprise' 
                    ? 'Start Chat' 
                    : 'Enterprise Only',
                  disabled: subscription?.plan !== 'enterprise',
                  url: '#'
                }}
              >
                <Text>Instant assistance</Text>
                <Text tone="subdued">
                  {subscription?.plan === 'enterprise'
                    ? 'Available now'
                    : 'Upgrade to Enterprise'}
                </Text>
              </CalloutCard>
            </Grid.Cell>
          </Grid>
        </Layout.Section>

        <Layout>
          <Layout.Section oneHalf>
            <Card>
              <BlockStack gap="400">
                <Text variant="headingMd" as="h2">Submit Support Ticket</Text>
                
                <TextField
                  label="Email"
                  value={email}
                  onChange={setEmail}
                  type="email"
                  error={errors.email}
                  placeholder="your@email.com"
                  autoComplete="email"
                />

                <TextField
                  label="Subject"
                  value={subject}
                  onChange={setSubject}
                  error={errors.subject}
                  placeholder="Brief description of your issue"
                  autoComplete="off"
                />

                <Select
                  label="Category"
                  options={[
                    { label: 'Technical Issue', value: 'technical' },
                    { label: 'Billing Question', value: 'billing' },
                    { label: 'Catalog Sync', value: 'catalog' },
                    { label: 'API Integration', value: 'api' },
                    { label: 'Feature Request', value: 'feature' },
                    { label: 'Other', value: 'other' }
                  ]}
                  value={category}
                  onChange={setCategory}
                />

                <Select
                  label="Priority"
                  options={[
                    { label: 'Low - General question', value: 'low' },
                    { label: 'Normal - Some impact on operations', value: 'normal' },
                    { label: 'High - Significant impact', value: 'high' },
                    { label: 'Urgent - Service is down', value: 'urgent' }
                  ]}
                  value={priority}
                  onChange={setPriority}
                />

                <TextField
                  label="Message"
                  value={message}
                  onChange={setMessage}
                  multiline={4}
                  error={errors.message}
                  placeholder="Please describe your issue in detail. Include any error messages, steps to reproduce, and what you expected to happen."
                  autoComplete="off"
                />

                <InlineStack gap="200">
                  <Button 
                    primary 
                    onClick={handleSubmit}
                    loading={fetcher.state === 'submitting'}
                  >
                    Submit Ticket
                  </Button>
                  {fetcher.state === 'submitting' && (
                    <Text tone="subdued">Submitting...</Text>
                  )}
                </InlineStack>
              </BlockStack>
            </Card>
          </Layout.Section>

          <Layout.Section oneHalf>
            <BlockStack gap="400">
              <Card>
                <BlockStack gap="400">
                  <Text variant="headingMd" as="h2">Quick Links</Text>
                  <BlockStack gap="300">
                    {quickLinks.map((link, index) => (
                      <Box key={index}>
                        <InlineStack align="space-between" blockAlign="center">
                          <BlockStack gap="100">
                            <InlineStack gap="200" blockAlign="center">
                              <Icon source={link.icon} />
                              <Link url={link.url} external>
                                {link.title}
                              </Link>
                              {link.requiresPlan && subscription?.plan !== link.requiresPlan && (
                                <Badge tone="info">{link.requiresPlan}</Badge>
                              )}
                            </InlineStack>
                            <Text tone="subdued" variant="bodySm">
                              {link.description}
                            </Text>
                          </BlockStack>
                        </InlineStack>
                        {index < quickLinks.length - 1 && <Box paddingBlockStart="300"><Divider /></Box>}
                      </Box>
                    ))}
                  </BlockStack>
                </BlockStack>
              </Card>

              <Card>
                <BlockStack gap="400">
                  <InlineStack align="space-between">
                    <Text variant="headingMd" as="h2">System Status</Text>
                    <Badge tone="success">All Systems Operational</Badge>
                  </InlineStack>
                  <BlockStack gap="200">
                    <InlineStack align="space-between">
                      <Text>API</Text>
                      <Badge tone="success">Operational</Badge>
                    </InlineStack>
                    <InlineStack align="space-between">
                      <Text>Catalog Sync</Text>
                      <Badge tone="success">Operational</Badge>
                    </InlineStack>
                    <InlineStack align="space-between">
                      <Text>Recommendations</Text>
                      <Badge tone="success">Operational</Badge>
                    </InlineStack>
                  </BlockStack>
                  <Link url="https://status.glamyouup.com" external>
                    View Status Page
                  </Link>
                </BlockStack>
              </Card>
            </BlockStack>
          </Layout.Section>
        </Layout>

        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <Text variant="headingMd" as="h2">Frequently Asked Questions</Text>
              <BlockStack gap="300">
                {faqs.map((faq) => (
                  <Box key={faq.id}>
                    <BlockStack gap="200">
                      <Button
                        plain
                        textAlign="left"
                        onClick={() => toggleFaq(faq.id)}
                        ariaExpanded={expandedFaq[faq.id]}
                        ariaControls={`faq-${faq.id}`}
                      >
                        <InlineStack gap="200" blockAlign="center">
                          <Icon 
                            source={expandedFaq[faq.id] ? ChevronDownIcon : ChevronRightIcon} 
                          />
                          <Text variant="bodyMd" fontWeight="semibold">
                            {faq.question}
                          </Text>
                        </InlineStack>
                      </Button>
                      <Collapsible
                        open={expandedFaq[faq.id]}
                        id={`faq-${faq.id}`}
                        transition={{ duration: '200ms', timingFunction: 'ease' }}
                      >
                        <Box paddingInlineStart="600">
                          <Text tone="subdued">{faq.answer}</Text>
                        </Box>
                      </Collapsible>
                    </BlockStack>
                    <Box paddingBlockStart="300">
                      <Divider />
                    </Box>
                  </Box>
                ))}
              </BlockStack>
            </BlockStack>
          </Card>
        </Layout.Section>

        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <Text variant="headingMd" as="h2">Troubleshooting Tips</Text>
              <List>
                <List.Item>
                  <Text fontWeight="semibold">Catalog not syncing?</Text> Ensure all products have images and are set to 'Active' status in your Shopify admin.
                </List.Item>
                <List.Item>
                  <Text fontWeight="semibold">Credits not resetting?</Text> Credits reset based on your billing cycle date, not calendar month.
                </List.Item>
                <List.Item>
                  <Text fontWeight="semibold">API rate limits?</Text> Enterprise plans have higher rate limits. Check headers for X-RateLimit-Remaining.
                </List.Item>
                <List.Item>
                  <Text fontWeight="semibold">Recommendations not showing?</Text> Verify the Glam You Up widget is installed on your product pages.
                </List.Item>
                <List.Item>
                  <Text fontWeight="semibold">Billing issues?</Text> Billing is managed through Shopify. Check your Shopify admin → Settings → Billing.
                </List.Item>
              </List>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}

export function ErrorBoundary({ error }) {
  return (
    <Page title="Help & Support">
      <Layout>
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Text variant="headingMd" as="h2">Unable to load support page</Text>
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