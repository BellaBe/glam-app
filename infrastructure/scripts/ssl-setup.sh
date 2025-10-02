#!/bin/bash
# SSL Certificate Setup for GLAM You Up

set -euo pipefail

DOMAIN=${1:-}
EMAIL=${2:-}

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: $0 domain.com admin@domain.com"
    exit 1
fi

echo "Setting up SSL for $DOMAIN..."

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yaml stop nginx || true

# Get certificate
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Create certificate directory
mkdir -p /opt/glam/infrastructure/nginx/certs

# Copy certificates
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/glam/infrastructure/nginx/certs/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/glam/infrastructure/nginx/certs/

# Set permissions
chmod 644 /opt/glam/infrastructure/nginx/certs/fullchain.pem
chmod 600 /opt/glam/infrastructure/nginx/certs/privkey.pem

# Update nginx config to use domain
sed -i "s/\${DOMAIN}/$DOMAIN/g" /opt/glam/infrastructure/nginx/nginx.conf

# Start nginx
docker-compose -f docker-compose.prod.yaml up -d nginx

# Setup auto-renewal
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'docker-compose -f /opt/glam/docker-compose.prod.yaml restart nginx'") | crontab -

echo "✅ SSL setup complete for $DOMAIN"
echo "✅ Auto-renewal configured via cron"