#!/bin/bash
set -e

# Configuration
# Load from environment variable or .env file if it exists
if [ -f .env.deploy ]; then
    source .env.deploy
fi

SERVER_IP="${SERVER_IP:?Set SERVER_IP in .env.deploy or environment}"
DOMAIN="${DOMAIN:-tsunami.supersistence.org}"
APP_NAME="${APP_NAME:-tsunami-viz}"

echo "Deploying $APP_NAME to Linode..."

# Build Docker image locally (optional test)
echo "Building Docker image locally for testing..."
docker build -t $APP_NAME:latest . || {
    echo "Docker build failed"
    exit 1
}

echo "Docker build successful"

# Test the image locally (optional)
read -p "Test the image locally? (y/N): " test_local
if [ "$test_local" = "y" ] || [ "$test_local" = "Y" ]; then
    echo "Starting local test..."
    docker run --rm -d -p 8050:8050 --name $APP_NAME-test $APP_NAME:latest
    echo "Test at: http://localhost:8050"
    echo "Press Enter when ready to continue..."
    read
    docker stop $APP_NAME-test
fi

# Copy files to server
echo "Copying files to server..."
rsync -avz --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.pytest_cache' --exclude='.env' --exclude='.env.*' \
    ./ deploy@$SERVER_IP:/opt/$APP_NAME/

# Deploy on server
echo "Deploying on server..."
ssh deploy@$SERVER_IP << EOF
set -e
cd /opt/$APP_NAME

echo "Stopping existing services..."
docker compose down || true

echo "Building and starting services..."
docker compose up -d --build

echo "Waiting for services to be ready..."
sleep 10

echo "Checking service health..."
docker compose ps
docker compose logs --tail=20 $APP_NAME

echo "Testing application..."
if curl -f http://127.0.0.1:8051 > /dev/null 2>&1; then
    echo "Application is responding"
else
    echo "Application is not responding"
    docker compose logs $APP_NAME
    exit 1
fi
EOF

echo "Deployment complete!"
echo "Your app should be available at:"
echo "   https://$DOMAIN"
echo ""
echo "To check logs:"
echo "   ssh deploy@$SERVER_IP 'cd /opt/$APP_NAME && docker compose logs -f'"
