#!/bin/bash
# Comprehensive Startup Script for MLOps Container
# This script ensures everything is properly initialized on container startup

set -e

echo "Starting MLOps Container Initialization..."

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

# Step 1: Run Python initialization script
log_info "Running container initialization..."
cd /app
python scripts/init_container.py

if [ $? -eq 0 ]; then
    log_success "Container initialization completed"
else
    log_error "Container initialization failed"
    exit 1
fi

# Step 2: Wait for services to start
log_info "Waiting for services to start..."
sleep 15

# Step 3: Test API health and trigger model loading
log_info "Testing API health and triggering model loading..."
for i in {1..5}; do
    if curl -s "http://localhost:8001/health" > /dev/null; then
        log_success "API is responding"
        
        # Try to make a test prediction to trigger model loading
        log_info "Triggering model loading with test prediction..."
        curl -s -X POST "http://localhost:8001/predict" \
            -H "Content-Type: application/json" \
            -d '{"longitude": -118.25, "latitude": 34.05, "housing_median_age": 35.0, "total_rooms": 1500.0, "total_bedrooms": 200.0, "population": 500.0, "households": 150.0, "median_income": 7.5}' \
            || log_warning "API prediction failed (expected on first run)"
        break
    else
        log_warning "API not ready yet, waiting..."
        sleep 5
    fi
done

# Step 4: Generate some initial metrics
log_info "Generating initial metrics..."
for i in {1..10}; do
    curl -s "http://localhost:8001/health" > /dev/null 2>&1 || true
    curl -s "http://localhost:8001/metrics" > /dev/null 2>&1 || true
    sleep 1
done

# Step 5: Check MLflow status and runs
log_info "Checking MLflow status and runs..."
if curl -s "http://localhost:5002" > /dev/null; then
    log_success "MLflow UI is accessible"
    
    # Check if we have MLflow runs
    if [ -d "/app/mlruns" ] && [ "$(ls -A /app/mlruns)" ]; then
        log_success "MLflow data directory contains runs"
        ls -la /app/mlruns/
    else
        log_warning "MLflow data directory is empty"
    fi
else
    log_warning "MLflow UI not accessible yet"
fi

# Step 6: Check Grafana status
log_info "Checking Grafana status..."
if curl -s "http://localhost:3000" > /dev/null; then
    log_success "Grafana is accessible"
else
    log_warning "Grafana not accessible yet"
fi

# Step 7: Check Prometheus status
log_info "Checking Prometheus status..."
if curl -s "http://localhost:9090/api/v1/targets" > /dev/null; then
    log_success "Prometheus is accessible"
else
    log_warning "Prometheus not accessible yet"
fi

# Step 8: Verify models directory
log_info "Checking models directory..."
if [ -d "/app/models" ] && [ "$(ls -A /app/models)" ]; then
    log_success "Models directory contains files"
    ls -la /app/models/
else
    log_warning "Models directory is empty"
fi

# Step 9: Run verification script
log_info "Running verification script..."
python scripts/verify_setup.py

if [ $? -eq 0 ]; then
    log_success "Verification completed successfully"
else
    log_warning "Verification found some issues"
fi

log_success "MLOps Container Initialization Complete!"
log_info "Services should be available at:"
log_info "  - API: http://localhost:8001"
log_info "  - MLflow: http://localhost:5002"
log_info "  - Prometheus: http://localhost:9090"
log_info "  - Grafana: http://localhost:3000 (admin/admin)"

log_info "Startup script completed successfully. Exiting..."
exit 0 