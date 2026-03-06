#!/bin/bash
set -e

DOMAIN="tsunami.supersistence.org"
SERVER_IP="172.236.244.235"

echo "Renewing SSL certificate for $DOMAIN..."

ssh root@$SERVER_IP << 'EOF'
set -e
certbot renew --nginx
echo "Certificate renewal complete."
certbot certificates
EOF
