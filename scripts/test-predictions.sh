#!/bin/bash
# Test Predictions and Check Dashboard Data
# This script tests the API predictions and helps diagnose dashboard issues

echo "🧪 Testing MLOps API Predictions and Dashboards"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to log messages
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

# Test 1: API Health
echo ""
log_info "Testing API Health..."
if curl -s "http://localhost:8001/health" > /dev/null; then
    log_success "API is healthy and responding"
else
    log_error "API health check failed"
    exit 1
fi

# Test 2: Make Predictions
echo ""
log_info "Testing Predictions..."

# Test case 1: San Francisco area
log_info "Test Case 1: San Francisco area (expensive)"
RESPONSE1=$(curl -s -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "longitude": -122.25,
    "latitude": 37.85,
    "housing_median_age": 25.0,
    "total_rooms": 2000.0,
    "total_bedrooms": 300.0,
    "population": 800.0,
    "households": 250.0,
    "median_income": 8.5
  }')

if [ $? -eq 0 ]; then
    log_success "Prediction 1 successful"
    echo "Response: $RESPONSE1"
else
    log_error "Prediction 1 failed"
fi

# Test case 2: Los Angeles area
log_info "Test Case 2: Los Angeles area (moderate)"
RESPONSE2=$(curl -s -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "longitude": -118.25,
    "latitude": 34.05,
    "housing_median_age": 35.0,
    "total_rooms": 1500.0,
    "total_bedrooms": 200.0,
    "population": 500.0,
    "households": 150.0,
    "median_income": 7.5
  }')

if [ $? -eq 0 ]; then
    log_success "Prediction 2 successful"
    echo "Response: $RESPONSE2"
else
    log_error "Prediction 2 failed"
fi

# Test case 3: Rural area
log_info "Test Case 3: Rural area (cheaper)"
RESPONSE3=$(curl -s -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "longitude": -120.0,
    "latitude": 36.0,
    "housing_median_age": 45.0,
    "total_rooms": 800.0,
    "total_bedrooms": 100.0,
    "population": 200.0,
    "households": 80.0,
    "median_income": 4.5
  }')

if [ $? -eq 0 ]; then
    log_success "Prediction 3 successful"
    echo "Response: $RESPONSE3"
else
    log_error "Prediction 3 failed"
fi

# Test 3: Check Metrics Endpoint
echo ""
log_info "Checking Metrics Endpoint..."
METRICS=$(curl -s "http://localhost:8001/metrics")
if [ $? -eq 0 ]; then
    log_success "Metrics endpoint is working"
    echo "Available metrics:"
    echo "$METRICS" | grep -E "^(#|http_|model_)" | head -20
else
    log_error "Metrics endpoint failed"
fi

# Test 4: Check Prometheus Targets
echo ""
log_info "Checking Prometheus Targets..."
PROM_TARGETS=$(curl -s "http://localhost:9090/api/v1/targets")
if [ $? -eq 0 ]; then
    log_success "Prometheus is responding"
    echo "Targets status:"
    echo "$PROM_TARGETS" | grep -o '"health":"[^"]*"' | head -5
else
    log_error "Prometheus not responding"
fi

# Test 5: Check MLflow Runs
echo ""
log_info "Checking MLflow Runs..."
if [ -d "/app/mlruns" ]; then
    RUN_COUNT=$(find /app/mlruns -name '*.yaml' 2>/dev/null | wc -l)
    log_info "Found $RUN_COUNT MLflow runs"
    
    if [ "$RUN_COUNT" -ge 5 ]; then
        log_success "Sufficient MLflow runs for dashboards"
    else
        log_warning "Only $RUN_COUNT runs found - dashboards may be empty"
    fi
else
    log_error "MLflow runs directory not found"
fi

# Test 6: Generate Some Traffic for Dashboards
echo ""
log_info "Generating traffic for dashboards..."
for i in {1..10}; do
    curl -s "http://localhost:8001/health" > /dev/null 2>&1
    curl -s "http://localhost:8001/metrics" > /dev/null 2>&1
    sleep 0.5
done
log_success "Generated traffic for metrics"

# Test 7: Check Dashboard Data
echo ""
log_info "Checking Dashboard Data Sources..."

# Check if Prometheus has data
PROM_QUERY=$(curl -s "http://localhost:9090/api/v1/query?query=up")
if [ $? -eq 0 ]; then
    log_success "Prometheus has data"
    echo "Sample query result: $PROM_QUERY"
else
    log_error "Prometheus query failed"
fi

# Check if API metrics are being collected
API_METRICS=$(curl -s "http://localhost:9090/api/v1/query?query=http_requests_total")
if [ $? -eq 0 ]; then
    log_success "API metrics are being collected"
    echo "API metrics: $API_METRICS"
else
    log_warning "API metrics not found in Prometheus"
fi

echo ""
log_info "Dashboard Troubleshooting Tips:"
echo "1. Check Grafana login: admin/admin"
echo "2. Verify Prometheus datasource is working"
echo "3. Check if metrics are flowing from API to Prometheus"
echo "4. Ensure MLflow models are generating prediction metrics"
echo ""
log_info "Test completed! Check the responses above for any issues." 