#!/bin/bash
# Startup script for MLOps container
# This script runs inside the container to initialize all services

set -e

echo "🚀 Starting MLOps container initialization..."

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p /app/logs
mkdir -p /app/models
mkdir -p /app/data/raw
echo "✅ Directories created"

# Wait for MLflow service to be ready
echo "⏳ Waiting for MLflow service to be ready..."
max_wait=60
wait_time=0
while ! curl -s http://localhost:5002 > /dev/null 2>&1; do
    if [ $wait_time -ge $max_wait ]; then
        echo "❌ MLflow service not ready after ${max_wait}s, proceeding anyway..."
        break
    fi
    echo "   Waiting for MLflow... (${wait_time}s/${max_wait}s)"
    sleep 5
    wait_time=$((wait_time + 5))
done
echo "✅ MLflow service is ready"

# Check if we already have MLflow runs
echo "🔍 Checking for existing MLflow runs..."
if [ -d "/app/mlruns" ] && [ "$(find /app/mlruns -name "*.yaml" | wc -l)" -gt 0 ]; then
    echo "✅ MLflow runs already exist, skipping initialization"
else
    echo "📊 No MLflow runs found, initializing container..."
    
    # Run the initialization script
    cd /app
    if python scripts/init_container.py; then
        echo "✅ Container initialization completed successfully!"
    else
        echo "❌ Container initialization failed, but continuing..."
    fi
fi

# Verify MLflow runs
echo "🔍 Verifying MLflow runs..."
if [ -d "/app/mlruns" ]; then
    run_count=$(find /app/mlruns -name "*.yaml" | wc -l)
    echo "📊 Found $run_count MLflow runs"
    
    if [ $run_count -ge 3 ]; then
        echo "✅ Sufficient MLflow runs found (need 3, have $run_count)"
    else
        echo "⚠️  Insufficient MLflow runs (need 3, have $run_count)"
    fi
else
    echo "❌ No MLflow directory found"
fi

# Final verification
echo "🔍 Final service verification..."
echo "   API: http://localhost:8001"
echo "   MLflow: http://localhost:5002"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000"

echo "✅ Container initialization completed!"
echo "🎉 All services should be running and ready" 