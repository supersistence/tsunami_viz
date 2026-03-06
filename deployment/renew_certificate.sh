#!/bin/bash
set -e

if [ -f .env.deploy ]; then
    source .env.deploy
fi

DOMAIN="${DOMAIN:-tsunami.supersistence.org}"
SERVER_IP="${SERVER_IP:?Set SERVER_IP in .env.deploy or environment}"

echo "Renewing SSL certificate for $DOMAIN..."

ssh root@$SERVER_IP << 'EOF'
set -e
certbot renew --nginx
echo "Certificate renewal complete."
certbot certificates
EOF
