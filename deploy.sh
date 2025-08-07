#!/bin/bash
set -e

# Configuration
DROPLET_IP="143.110.144.44"
DOMAIN="tsunami.supersistence.org"
APP_NAME="tsunami-viz"

echo "🚀 Deploying $APP_NAME to DigitalOcean Droplet..."

# Check if droplet IP is configured
if [ "$DROPLET_IP" = "YOUR_DROPLET_IP" ]; then
    echo "❌ Please configure DROPLET_IP in deploy.sh"
    exit 1
fi

# Build Docker image locally (optional test)
echo "🔨 Building Docker image locally for testing..."
docker build -t $APP_NAME:latest . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Docker build successful"

# Test the image locally (optional)
read -p "🧪 Test the image locally? (y/N): " test_local
if [ "$test_local" = "y" ] || [ "$test_local" = "Y" ]; then
    echo "🧪 Starting local test..."
    docker run --rm -d -p 8050:8050 --name $APP_NAME-test $APP_NAME:latest
    echo "🌐 Test at: http://localhost:8050"
    echo "Press Enter when ready to continue..."
    read
    docker stop $APP_NAME-test
fi

# Copy files to droplet
echo "📤 Copying files to droplet..."
rsync -avz --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.pytest_cache' \
    ./ root@$DROPLET_IP:/opt/$APP_NAME/

# Deploy on droplet
echo "🔄 Deploying on droplet..."
ssh root@$DROPLET_IP << EOF
set -e
cd /opt/$APP_NAME

echo "🛑 Stopping existing services..."
docker-compose down || true

echo "🔨 Building and starting services..."
docker-compose up -d --build

echo "⏱️ Waiting for services to be ready..."
sleep 10

echo "🔍 Checking service health..."
docker-compose ps
docker-compose logs --tail=20 $APP_NAME

echo "🧪 Testing application..."
if curl -f http://localhost:8050 > /dev/null 2>&1; then
    echo "✅ Application is responding locally"
else
    echo "❌ Application is not responding locally"
    docker-compose logs $APP_NAME
    exit 1
fi
EOF

echo "✅ Deployment complete!"
echo "🌐 Your app should be available at:"
echo "   http://$DOMAIN (redirects to HTTPS)"
echo "   https://$DOMAIN"
echo ""
echo "🔍 To check logs:"
echo "   ssh root@$DROPLET_IP 'docker-compose -f /opt/$APP_NAME/docker-compose.yml logs -f'"
echo ""
echo "🔧 To manage the deployment:"
echo "   ssh root@$DROPLET_IP 'cd /opt/$APP_NAME && docker-compose [up|down|restart|logs]'"