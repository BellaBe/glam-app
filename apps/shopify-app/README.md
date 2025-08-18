# Shopify App Template - Remix

This is a template for building a [Shopify app](https://shopify.dev/docs/apps/getting-started) using the [Remix](https://remix.run) framework.

Rather than cloning this repo, you can use your preferred package manager and the Shopify CLI with [these steps](https://shopify.dev/docs/apps/getting-started/create).

Visit the [`shopify.dev` documentation](https://shopify.dev/docs/api/shopify-app-remix) for more details on the Remix app package.

## Quick start

### Prerequisites

1. You must install Node.js and version > 18.0.0
2. You must install Ruby and version > 3.0.0
3. You must [create a Shopify partner account](https://partners.shopify.com/signup) if you don’t have one.
4. You must create a store for testing if you don't have one, either a [development store](https://help.shopify.com/en/partners/dashboard/development-stores#create-a-development-store) or a [Shopify Plus sandbox store](https://help.shopify.com/en/partners/dashboard/managing-stores/plus-sandbox-store).

### Setup

If you used the CLI to create the template, you can skip this section.

Using yarn:

```shell
yarn install
```

Using npm:

```shell
npm install
```

Using pnpm:

```shell
pnpm install
```

### Local Development

Using yarn:

```shell
yarn dev
```

Using npm:

```shell
npm run dev
```

Using pnpm:

```shell
pnpm run dev
```

Press P to open the URL to your app. Once you click install, you can start development.

Local development is powered by [the Shopify CLI](https://shopify.dev/docs/apps/tools/cli). It logs into your partners account, connects to an app, provides environment variables, updates remote config, creates a tunnel and provides commands to generate extensions.

### Authenticating and querying data

To authenticate and query data you can use the `shopify` const that is exported from `/app/shopify.server.js`:

```js
export async function loader({ request }) {
  const { admin } = await shopify.authenticate.admin(request);

  const response = await admin.graphql(`
    {
      products(first: 25) {
        nodes {
          title
          description
        }
      }
    }`);

  const {
    data: {
      products: { nodes },
    },
  } = await response.json();

  return json(nodes);
}
```

This template come preconfigured with examples of:

1. Setting up your Shopify app in [/app/shopify.server.ts](https://github.com/Shopify/shopify-app-template-remix/blob/main/app/shopify.server.ts)
2. Querying data using Graphql. Please see: [/app/routes/app.\_index.tsx](https://github.com/Shopify/shopify-app-template-remix/blob/main/app/routes/app._index.tsx).
3. Responding to mandatory webhooks in [/app/routes/webhooks.tsx](https://github.com/Shopify/shopify-app-template-remix/blob/main/app/routes/webhooks.tsx)

Please read the [documentation for @shopify/shopify-app-remix](https://www.npmjs.com/package/@shopify/shopify-app-remix#authenticating-admin-requests) to understand what other API's are available.

## Deployment

### Apps permission setting

To configure GraphQL access scopes in a TOML file, you need to ensure that you include the necessary permissions for the app. Here's a step-by-step guide to setting up the access scopes correctly:

1. Locate the access_scopes section: In TOML configuration file, find the section where you specify access scopes. If it's not already present, you may need to add it.
2. Define the scopes: Within the access_scopes section, specify the permissions required for your application to interact with GraphQL. These permissions typically include read and write access to various resources. Here's an example of how you can specify these scopes
   [access_scopes]
   scopes = "read_metaobject_definitions,read_metaobjects,read_orders,write_metaobject_definitions,write_metaobjects,write_orders,write_products"

### Apps special setting

#### Setting up .env Variables

1. Create a .env File: In the root directory of your React app, create a file named .env.
2. Define Variables: Inside the .env file, define your variables like this:

SHOPIFY\*API_KEY=your_api_key_here
SHOPIFY_API_SECRET=your_api_secret_here
SHOPIFY_GLAMYOUUP_ID=\*\**
AI*SERVER_URL=\*\*\*

#### Setting up Server URLs

For setting up AI server URL and Remix server URL, you'll typically follow similar steps.

1. Configuration File or Environment Variables: Depending on how your React app is structured, you might have a configuration file where you define these URLs or you might directly use environment variables.
2. Define Server URLs(AI server and Remix server):

- extensions/glam-you-up/script.js

### Application Storage

This template uses [Prisma](https://www.prisma.io/) to store session data, by default using an [SQLite](https://www.sqlite.org/index.html) database.
The database is defined as a Prisma schema in `prisma/schema.prisma`.

This use of SQLite works in production if your app runs as a single instance.
The database that works best for you depends on the data your app needs and how it is queried.
You can run your database of choice on a server yourself or host it with a SaaS company.

#### Database migration

1. Run the command `npm run prisma migrate dev` to migrate the db with the schema.
2. Run the command `npm run prisma studio` to visit the db table.

### Build

Remix handles building the app for you, by running the command below with the package manager of your choice:

Using yarn:

```shell
yarn build
```

Using npm:

```shell
npm run build
```

Using pnpm:

```shell
pnpm run build
```

### Test on the local environment

Using yarn:

```shell
yarn start
```

Using npm:

```shell
npm run start
```

Using pnpm:

```shell
pnpm run start
```

### Hosting for the test

Remix-serve will start with `http://localhost:3000` on your local environment.
You can host your app with ngrok or any other services (Fro exmaple: ngork http 3000)
Go to your partner account and change the app hosting URL on the configuration of the app.

### Hosting

When you're ready to set up your app in production, you can follow [our deployment documentation](https://shopify.dev/docs/apps/deployment/web) to host your app on a cloud provider.

When you reach the step for [setting up environment variables](https://shopify.dev/docs/apps/deployment/web#set-env-vars), you also need to set the variable `NODE_ENV=production`.

### Upload local app's extensions and environment to live shopify app store

To do that, you can run the `deploy` CLI command.

Using yarn:

```shell
yarn deploy
```

Using npm:

```shell
npm run deploy
```

Using pnpm:

```shell
pnpm run deploy
```

## Resources

- [Remix Docs](https://remix.run/docs/en/v1)
- [Shopify App Remix](https://shopify.dev/docs/api/shopify-app-remix)
- [Introduction to Shopify apps](https://shopify.dev/docs/apps/getting-started)
- [App authentication](https://shopify.dev/docs/apps/auth)
- [Shopify CLI](https://shopify.dev/docs/apps/tools/cli)
- [App extensions](https://shopify.dev/docs/apps/app-extensions/list)
- [Shopify Functions](https://shopify.dev/docs/api/functions)
- [Getting started with internationalizing your app](https://shopify.dev/docs/apps/best-practices/internationalization/getting-started)
