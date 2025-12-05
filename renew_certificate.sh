#!/bin/bash
set -e

# Certificate renewal script for tsunami visualization app
# Run this on the server when the SSL certificate expires

DOMAIN="tsunami.supersistence.org"
DROPLET_IP="143.110.144.44"
APP_NAME="tsunami-viz"

echo "🔒 Renewing SSL certificate for $DOMAIN..."

# Check if running on server or locally
if [ "$(hostname)" != "$(ssh -o ConnectTimeout=5 root@$DROPLET_IP 'hostname' 2>/dev/null || echo 'not-server')" ]; then
    echo "📡 Connecting to server to renew certificate..."
    
    ssh root@$DROPLET_IP << 'EOF'
        set -e
        DOMAIN="tsunami.supersistence.org"
        APP_NAME="tsunami-viz"
        
        echo "🛑 Stopping nginx to free port 80 for certificate renewal..."
        cd /opt/$APP_NAME
        docker-compose stop nginx || true
        
        echo "🔄 Renewing certificate..."
        certbot certonly --standalone --force-renewal -d $DOMAIN
        
        echo "🔗 Copying SSL certificates (Docker can't use symlinks)..."
        mkdir -p /opt/$APP_NAME/nginx/ssl
        rm -f /opt/$APP_NAME/nginx/ssl/fullchain.pem
        rm -f /opt/$APP_NAME/nginx/ssl/privkey.pem
        cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/$APP_NAME/nginx/ssl/fullchain.pem
        cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/$APP_NAME/nginx/ssl/privkey.pem
        chmod 644 /opt/$APP_NAME/nginx/ssl/fullchain.pem
        chmod 600 /opt/$APP_NAME/nginx/ssl/privkey.pem
        
        echo "🚀 Restarting nginx..."
        docker-compose up -d nginx
        
        echo "✅ Certificate renewed successfully!"
        echo ""
        echo "📋 Certificate details:"
        certbot certificates
        
        echo ""
        echo "🧪 Testing SSL connection..."
        sleep 3
        if curl -f https://$DOMAIN > /dev/null 2>&1; then
            echo "✅ HTTPS is working correctly!"
        else
            echo "⚠️  HTTPS test failed - check nginx logs"
            docker-compose logs nginx
        fi
EOF
    
    echo ""
    echo "✅ Certificate renewal complete!"
    echo "🌐 Test at: https://$DOMAIN"
else
    echo "🔄 Renewing certificate locally on server..."
    
    cd /opt/$APP_NAME
    
    echo "🛑 Stopping nginx to free port 80 for certificate renewal..."
    docker-compose stop nginx || true
    
    echo "🔄 Renewing certificate..."
    certbot certonly --standalone --force-renewal -d $DOMAIN
    
    echo "🔗 Copying SSL certificates (Docker can't use symlinks)..."
    mkdir -p /opt/$APP_NAME/nginx/ssl
    rm -f /opt/$APP_NAME/nginx/ssl/fullchain.pem
    rm -f /opt/$APP_NAME/nginx/ssl/privkey.pem
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/$APP_NAME/nginx/ssl/fullchain.pem
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/$APP_NAME/nginx/ssl/privkey.pem
    chmod 644 /opt/$APP_NAME/nginx/ssl/fullchain.pem
    chmod 600 /opt/$APP_NAME/nginx/ssl/privkey.pem
    
    echo "🚀 Restarting nginx..."
    docker-compose up -d nginx
    
    echo "✅ Certificate renewed successfully!"
    echo ""
    echo "📋 Certificate details:"
    certbot certificates
fi

