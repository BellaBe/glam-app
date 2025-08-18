export const GET_PRODUCTS_QUERY = `#graphql
query products($after: String) {
  products(first: 250, after: $after) {
    edges {
      node {
        id
        title
        featuredImage {
          id
          originalSrc
        }
        variants(first: 250) {
          edges {
            node {
              id
              image {
                id
                originalSrc
              }
            }
          }
        }
      }
      cursor
    }
    pageInfo {
      hasNextPage
    }
  }
}`;

export const GET_SHOP_INFO = `#graphql
  query getShopInfo {
    shop {
      id
      name
      url
      email
      currencyCode
      primaryDomain {
        url
        host
      }
      plan {
        displayName
        partnerDevelopment
        shopifyPlus
      }
      myshopifyDomain
      contactEmail
      billingAddress {
        country
        countryCodeV2
        city
        province
        provinceCode
        zip
      }
    }
    }
`;

export const GET_A_METAOBJECT_BY_HANDLE = `
{
  metaobjectByHandle(handle: {
    type: "$app:gyu_status",
    handle: "gyu_billing_status"
  }) {
    displayName
    id
    handle
  }
}`;

export const GET_A_METAOBJECTDEFINITION_BY_TYPE = `
{
  metaobjectDefinitionByType(type: "$app:gyu_status") {
    id
  }
}`;

export const CREATE_NEW_METAOBJECT_DEFINITION = `#graphql
mutation metaobjectDefinitionCreate($definition: MetaobjectDefinitionCreateInput!) {
  metaobjectDefinitionCreate(definition: $definition) {
    metaobjectDefinition {
      id
      name
      type
    }
    userErrors {
      field
      message
    }
  }
}`;

export const CREATE_NEW_METAOBJECT = `#graphql
mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
  metaobjectCreate(metaobject: $metaobject) {
    metaobject {
      id
      type
    }
    userErrors {
      field
      message
    }
  }
}`;

export const DELETE_A_METAOBJECT_DEFINITION_BY_ID = `#graphql
mutation metaobjectDefinitionDelete($id: ID!) {
  metaobjectDefinitionDelete(id: $id) {
    deletedId
    userErrors {
      field
      message
    }
  }
}`;

export const CREATE_APP_SUBSCRIPTION = `#graphql
mutation AppSubscriptionCreate($name: String!, $lineItems: [AppSubscriptionLineItemInput!]!, $returnUrl: URL!, $test: Boolean!, $trialDays: Int!) {
  appSubscriptionCreate(name: $name, returnUrl: $returnUrl, lineItems: $lineItems, test: $test, trialDays: $trialDays) {
    userErrors {
      field
      message
    }
    appSubscription {
      id
      lineItems {
        id
        plan {
          pricingDetails
          __typename
        }
      }
      currentPeriodEnd
      status
    }
    confirmationUrl
  }
}`;

export const CREATE_APP_ONE_TIME_SUBSCRIPTION = `#graphql
mutation appPurchaseOneTimeCreate($name: String!, $returnUrl: URL!, $price: MoneyInput!, $test: Boolean!) {
  appPurchaseOneTimeCreate(name: $name, returnUrl: $returnUrl, price: $price, test: $test) {
    userErrors {
      field
      message
    }
    appPurchaseOneTime {
      createdAt
      id
      name
      price {
        amount
        currencyCode
      }
      status
      test
    }
    confirmationUrl
  }
}`;

export const CHECK_FOR_SUBSCRIPTION = `#graphql
{
  currentAppInstallation {
    activeSubscriptions {
    id
    lineItems {
      id
      plan {
        pricingDetails {
          ... on AppUsagePricing {
          __typename
          }
        }
      }
    }
    status
    currentPeriodEnd
    name
    }
  }
}`;

export const CANCEL_SUBSCRIPTION = `#graphql
mutation AppSubscriptionCancel($id: ID!) {
  appSubscriptionCancel(id: $id) {
    userErrors {
      field
      message
    }
    appSubscription {
      id
      status
    }
  }
}`;

export function GET_ORDERS_COUNT(startDate, endDate) {
  return `#graphql
  {
    orders(query: "created_at:>='${startDate}' AND created_at:<'${endDate}'") {
      nodes {
        id
      }
    }
  }`;
}
