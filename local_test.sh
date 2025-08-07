#!/bin/bash
set -e

echo "🧪 Local Docker Test for Tsunami Viz"
echo "===================================="

# Clean up any existing test containers
echo "🧹 Cleaning up existing test containers..."
docker stop tsunami-viz-test 2>/dev/null || true
docker rm tsunami-viz-test 2>/dev/null || true

# Build the image
echo "🔨 Building Docker image..."
docker build -t tsunami-viz:test .

# Run the container
echo "🚀 Starting container..."
docker run -d \
    --name tsunami-viz-test \
    -p 8050:8050 \
    -v "$(pwd)/data:/app/data:ro" \
    tsunami-viz:test

# Wait for startup
echo "⏱️ Waiting for application to start..."
sleep 10

# Test the application
echo "🧪 Testing application..."
python3 test_deployment.py

# Show container logs
echo ""
echo "📋 Container logs (last 20 lines):"
docker logs --tail=20 tsunami-viz-test

# Show container stats
echo ""
echo "📊 Container stats:"
docker stats --no-stream tsunami-viz-test

echo ""
echo "🌐 Application is running at: http://localhost:8050"
echo "🔍 Check logs: docker logs -f tsunami-viz-test"
echo "🛑 Stop test: docker stop tsunami-viz-test && docker rm tsunami-viz-test"
echo ""
echo "✅ Local test complete! Ready for production deployment."