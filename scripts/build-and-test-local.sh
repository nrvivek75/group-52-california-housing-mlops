#!/bin/bash
# Local Build and Test Script for MLOps Container
# This script builds the image locally and tests it

set -e

echo "Building and testing MLOps container locally..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Build the image
log_info "Building Docker image..."
docker build -t mlops-local:latest .

if [ $? -eq 0 ]; then
    log_success "Docker image built successfully"
else
    log_error "Docker build failed"
    exit 1
fi

# Step 2: Stop any existing container
log_info "Stopping existing container..."
docker stop mlops-test 2>/dev/null || true
docker rm mlops-test 2>/dev/null || true

# Step 3: Run the container
log_info "Starting container for testing..."
docker run -d \
    --name mlops-test \
    -p 8001:8001 \
    -p 5002:5002 \
    -p 9090:9090 \
    -p 3000:3000 \
    mlops-local:latest

if [ $? -eq 0 ]; then
    log_success "Container started successfully"
else
    log_error "Failed to start container"
    exit 1
fi

# Step 4: Wait for initialization
log_info "Waiting for container initialization..."
sleep 30

# Step 5: Check container logs
log_info "Container logs:"
docker logs mlops-test

# Step 6: Test services
log_info "Testing services..."

# Test API
if curl -s "http://localhost:8001/health" > /dev/null; then
    log_success "API is responding"
else
    log_error "API not responding"
fi

# Test MLflow
if curl -s "http://localhost:5002" > /dev/null; then
    log_success "MLflow is responding"
else
    log_error "MLflow not responding"
fi

# Test Prometheus
if curl -s "http://localhost:9090/api/v1/targets" > /dev/null; then
    log_success "Prometheus is responding"
else
    log_error "Prometheus not responding"
fi

# Test Grafana
if curl -s "http://localhost:3000" > /dev/null; then
    log_success "Grafana is responding"
else
    log_error "Grafana not responding"
fi

# Step 7: Check MLflow runs
log_info "Checking MLflow runs..."
docker exec mlops-test ls -la /app/mlruns/ 2>/dev/null || log_warning "Cannot check MLflow directory"

# Step 8: Check Grafana dashboards
log_info "Checking Grafana dashboards..."
docker exec mlops-test ls -la /app/grafana/provisioning/dashboards/ 2>/dev/null || log_warning "Cannot check Grafana directory"

log_success "Local testing completed!"
log_info "You can now access:"
log_info "  - API: http://localhost:8001"
log_info "  - MLflow: http://localhost:5002"
log_info "  - Prometheus: http://localhost:9090"
log_info "  - Grafana: http://localhost:3000 (admin/admin)"

log_info "To stop the test container: docker stop mlops-test"
log_info "To remove the test container: docker rm mlops-test" 