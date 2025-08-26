# apps/shopify-app/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY apps/shopify-app/package*.json ./apps/shopify-app/

# Install dependencies
RUN npm ci --only=production

# Copy app code
COPY apps/shopify-app ./apps/shopify-app

# Build the app
WORKDIR /app/apps/shopify-app
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy built app
COPY --from=builder /app/apps/shopify-app/build ./build
COPY --from=builder /app/apps/shopify-app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/apps/shopify-app/package*.json ./

# Prisma files
COPY apps/shopify-app/prisma ./prisma

EXPOSE 3000

CMD ["npm", "start"]
