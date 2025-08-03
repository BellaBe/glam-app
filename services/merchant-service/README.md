# Merchant Service

Merchant identity and consent management service for the GLAM platform.

## Overview

The Merchant Service manages:
- Merchant identity and installation lifecycle
- Consent settings (data access, auto-sync, TOS)
- OAuth sync after Shopify installation
- Activity tracking for analytics
- Status management (PENDING, ACTIVE, SUSPENDED, DEACTIVATED)

## Port Configuration

- Internal Port: 8013 (container)
- External Port: 8113 (local development)
- Database Port: 5413
- Redis Port: 6313
- NATS Port: 4213

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Set up environment:
```bash
cp .env.example .env
# Edit .env with your secrets
```

3. Generate Prisma client:
```bash
prisma generate
```

4. Run migrations:
```bash
prisma migrate dev
```

5. Start service:
```bash
