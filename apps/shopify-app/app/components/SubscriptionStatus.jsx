import { CalloutCard, Text, Badge, InlineStack, BlockStack } from "@shopify/polaris";

export default function SubscriptionStatus({ subscription, onStartTrial, onViewPlans }) {
  const getStatusContent = () => {
    if (subscription.status === "inactive") {
      return {
        title: "Start your free 14-day trial",
        description: "Get 500 credits to test selfie-based recommendations",
        primaryAction: {
          content: "Start Free Trial",
          onAction: onStartTrial,
        },
        tone: "info",
      };
    }

    if (subscription.status === "trial") {
      const daysLeft = Math.ceil(
        (new Date(subscription.trialEndsAt) - new Date()) / (1000 * 60 * 60 * 24)
      );

      return {
        title: `Free trial: ${daysLeft} days remaining`,
        description: "Choose a plan to continue after your trial ends",
        primaryAction: {
          content: "View Plans",
          onAction: onViewPlans,
        },
        tone: daysLeft <= 3 ? "warning" : "info",
      };
    }

    if (subscription.status === "active") {
      return {
        title: `${
          subscription.plan.charAt(0).toUpperCase() + subscription.plan.slice(1)
        } Plan Active`,
        description: `Next billing date: ${new Date(
          subscription.nextBillingDate
        ).toLocaleDateString()}`,
        primaryAction: {
          content: "Manage Billing",
          onAction: onViewPlans,
        },
        tone: "success",
      };
    }

    if (subscription.status === "expired") {
      return {
        title: "Trial expired",
        description: "Choose a plan to continue using Glam You Up",
        primaryAction: {
          content: "View Plans",
          onAction: onViewPlans,
        },
        tone: "critical",
      };
    }
  };

  const content = getStatusContent();

  return (
    <CalloutCard
      title={content.title}
      illustration="https://cdn.shopify.com/s/files/1/0583/6465/7734/files/tag.svg?v=1701930959"
      primaryAction={content.primaryAction}
    >
      <Text>{content.description}</Text>
    </CalloutCard>
  );
}
