#!/bin/bash

# 🔧 Permanent Fix for Recurring SSL and MapTiler Issues
# This script addresses the root causes and implements permanent solutions

echo "🚀 Starting Permanent Fix for Recurring Issues..."
echo "=================================================="

# Check if we're running on the server
if [[ $(hostname) == *"tsunami"* ]] || [[ -d "/opt/tsunami-viz" ]]; then
    echo "✅ Running on production server"
    BASE_DIR="/opt/tsunami-viz"
else
    echo "✅ Running locally - will deploy to server"
    BASE_DIR="."
fi

cd "$BASE_DIR" || exit 1

echo ""
echo "🔧 SOLUTION 1: Fix Docker Compose Configuration"
echo "=============================================="

# Create the corrected docker-compose.yml with all necessary configurations
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - tsunami-viz
    restart: unless-stopped
    networks:
      - app-network

  tsunami-viz:
    build: .
    ports:
      - '8050:8050'  # Direct access for debugging
    environment:
      - PORT=8050
      - DEBUG=False
    env_file: .env  # CRITICAL: Load environment variables
    volumes:
      - ./data:/app/data:ro
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8050', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  app-network:
    driver: bridge
EOF

echo "✅ Fixed docker-compose.yml with env_file and port mapping"

echo ""
echo "🔧 SOLUTION 2: Permanent SSL Certificate Setup"
echo "============================================="

# Create SSL certificate management script
mkdir -p nginx/ssl

# Copy SSL certificates (the permanent way - no symlinks)
if [[ -d "/etc/letsencrypt/live" ]]; then
    DOMAIN=$(ls /etc/letsencrypt/live/ | grep -v README | head -1)
    if [[ -n "$DOMAIN" ]]; then
        echo "📋 Found SSL domain: $DOMAIN"
        
        # Copy actual certificate files (not symlinks)
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" nginx/ssl/fullchain.pem 2>/dev/null || echo "⚠️  Could not copy fullchain.pem"
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" nginx/ssl/privkey.pem 2>/dev/null || echo "⚠️  Could not copy privkey.pem"
        
        # Set proper permissions
        chmod 644 nginx/ssl/fullchain.pem 2>/dev/null
        chmod 600 nginx/ssl/privkey.pem 2>/dev/null
        
        echo "✅ SSL certificates copied to nginx/ssl/"
        ls -la nginx/ssl/
    else
        echo "⚠️  No SSL certificates found in /etc/letsencrypt/live/"
    fi
else
    echo "⚠️  /etc/letsencrypt not found - SSL certificates need to be set up"
fi

echo ""
echo "🔧 SOLUTION 3: Automatic SSL Certificate Renewal"
echo "==============================================="

# Create SSL renewal script
cat > renew_ssl.sh << 'EOF'
#!/bin/bash
# Automatic SSL certificate renewal and deployment

echo "🔄 Renewing SSL certificates..."

# Find the domain
DOMAIN=$(ls /etc/letsencrypt/live/ | grep -v README | head -1)

if [[ -n "$DOMAIN" ]]; then
    echo "📋 Renewing certificates for domain: $DOMAIN"
    
    # Renew certificates
    certbot renew --quiet
    
    # Copy renewed certificates (avoid symlink issues)
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" /opt/tsunami-viz/nginx/ssl/fullchain.pem
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" /opt/tsunami-viz/nginx/ssl/privkey.pem
    
    # Set permissions
    chmod 644 /opt/tsunami-viz/nginx/ssl/fullchain.pem
    chmod 600 /opt/tsunami-viz/nginx/ssl/privkey.pem
    
    # Restart nginx to load new certificates
    cd /opt/tsunami-viz
    docker-compose restart nginx
    
    echo "✅ SSL certificates renewed and deployed"
else
    echo "❌ No domain found for SSL renewal"
fi
EOF

chmod +x renew_ssl.sh
echo "✅ Created automatic SSL renewal script"

echo ""
echo "🔧 SOLUTION 4: Verify Environment Variables"
echo "=========================================="

# Ensure .env file has correct format
if [[ ! -f ".env" ]]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# MapTiler API Configuration
MAPTILER_API_KEY=8OKLKpQl2oc8hiu0NwT2

# App Configuration
PORT=8050
DEBUG=False
EOF
fi

echo "📋 Current .env file:"
cat .env
echo ""

echo ""
echo "🔧 SOLUTION 5: Container Health Monitoring"
echo "========================================"

# Create monitoring script
cat > monitor_health.sh << 'EOF'
#!/bin/bash
# Monitor and auto-restart containers if they fail

echo "🔍 Checking container health..."

# Check if nginx is running
if ! docker-compose ps nginx | grep -q "Up"; then
    echo "⚠️  Nginx container is down - restarting..."
    docker-compose restart nginx
fi

# Check if tsunami-viz is running
if ! docker-compose ps tsunami-viz | grep -q "Up"; then
    echo "⚠️  Tsunami-viz container is down - restarting..."
    docker-compose restart tsunami-viz
fi

# Check if SSL certificates exist
if [[ ! -f "nginx/ssl/fullchain.pem" ]] || [[ ! -f "nginx/ssl/privkey.pem" ]]; then
    echo "⚠️  SSL certificates missing - running SSL fix..."
    ./renew_ssl.sh
fi

echo "✅ Health check complete"
EOF

chmod +x monitor_health.sh
echo "✅ Created container health monitoring script"

echo ""
echo "🔧 APPLYING FIXES NOW"
echo "==================="

# Stop all containers
echo "🛑 Stopping containers..."
docker-compose down

# Rebuild and restart with new configuration
echo "🔄 Rebuilding and restarting containers..."
docker-compose up -d

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 15

# Check final status
echo ""
echo "📊 FINAL STATUS:"
echo "==============="
docker-compose ps

echo ""
echo "🌐 Testing access..."
if curl -s http://localhost:8050 > /dev/null; then
    echo "✅ HTTP access working"
else
    echo "❌ HTTP access failed"
fi

if curl -s -k https://localhost > /dev/null; then
    echo "✅ HTTPS access working"
else
    echo "❌ HTTPS access failed"
fi

echo ""
echo "🎉 PERMANENT FIXES APPLIED!"
echo "=========================="
echo ""
echo "💡 To prevent future issues:"
echo "   1. Run './monitor_health.sh' regularly (or set up a cron job)"
echo "   2. Run './renew_ssl.sh' monthly for SSL renewal"
echo "   3. The fixed docker-compose.yml will persist environment variables"
echo ""
echo "🌐 Your site should now be accessible at:"
echo "   - HTTP: http://tsunami.supersistence.org:8050 (direct)"
echo "   - HTTPS: https://tsunami.supersistence.org (via nginx)"
EOF

chmod +x fix_recurring_issues.sh
echo "✅ Created permanent fix script"