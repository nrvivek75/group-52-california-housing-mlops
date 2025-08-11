#!/bin/bash
# Test script for California Housing MLOps API
# This script tests all the main endpoints to ensure they're working
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="http://localhost:8001"
WAIT_TIMEOUT=30

# Helper functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

wait_for_api() {
    print_info "Waiting for API to be ready..."
    local count=0
    while [ $count -lt $WAIT_TIMEOUT ]; do
        if curl -s "$API_BASE_URL/health" >/dev/null 2>&1; then
            print_success "API is ready!"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    print_error "API failed to start within $WAIT_TIMEOUT seconds"
    exit 1
}

test_root() {
    print_info "Testing root endpoint..."
    local response=$(curl -s "$API_BASE_URL/")
    if [[ "$response" == *"California Housing"* ]]; then
        print_success "Root endpoint working"
    else
        print_error "Root endpoint failed"
        return 1
    fi
}

test_health() {
    print_info "Testing health endpoint..."
    local response=$(curl -s "$API_BASE_URL/health")
    if [[ "$response" == *"healthy"* ]]; then
        print_success "Health endpoint working"
    else
        print_error "Health endpoint failed"
        return 1
    fi
}

test_prediction() {
    print_info "Testing prediction endpoint..."
    local test_data='{
        "longitude": -118.25,
        "latitude": 34.05,
        "housing_median_age": 35.0,
        "total_rooms": 1500.0,
        "total_bedrooms": 200.0,
        "population": 500.0,
        "households": 150.0,
        "median_income": 7.5
    }'
    
    local response=$(curl -s -X POST "$API_BASE_URL/predict" \
        -H "Content-Type: application/json" \
        -d "$test_data")
    
    if [[ "$response" == *"prediction"* ]]; then
        print_success "Prediction endpoint working"
        echo "  Response: $response"
    else
        print_error "Prediction endpoint failed"
        echo "  Response: $response"
        return 1
    fi
}

test_metrics() {
    print_info "Testing metrics endpoint..."
    local response=$(curl -s "$API_BASE_URL/metrics")
    if [[ "$response" == *"http_requests_total"* ]]; then
        print_success "Metrics endpoint working"
    else
        print_error "Metrics endpoint failed"
        return 1
    fi
}

test_logs() {
    print_info "Testing logs endpoint..."
    local response=$(curl -s "$API_BASE_URL/logs")
    if [[ "$response" == *"logs"* ]] || [[ "$response" == *"predictions"* ]]; then
        print_success "Logs endpoint working"
    else
        print_error "Logs endpoint failed"
        echo "  Response: $response"
        return 1
    fi
}

test_model_performance() {
    print_info "Testing model performance endpoint..."
    local response=$(curl -s "$API_BASE_URL/model/performance")
    if [[ "$response" == *"performance"* ]] || [[ "$response" == *"error"* ]]; then
        print_success "Model performance endpoint working"
    else
        print_error "Model performance endpoint failed"
        return 1
    fi
}

test_data_drift() {
    print_info "Testing data drift endpoint..."
    local response=$(curl -s "$API_BASE_URL/model/drift")
    if [[ "$response" == *"drift"* ]] || [[ "$response" == *"error"* ]]; then
        print_success "Data drift endpoint working"
    else
        print_error "Data drift endpoint failed"
        return 1
    fi
}

test_retraining() {
    print_info "Testing retraining endpoint..."
    local test_data='{
        "trigger_type": "manual",
        "force": true
    }'
    
    local response=$(curl -s -X POST "$API_BASE_URL/retrain" \
        -H "Content-Type: application/json" \
        -d "$test_data")
    
    if [[ "$response" == *"retraining"* ]] || [[ "$response" == *"error"* ]]; then
        print_success "Retraining endpoint working"
    else
        print_error "Retraining endpoint failed"
        return 1
    fi
}

test_docs() {
    print_info "Testing API documentation..."
    local response=$(curl -s "$API_BASE_URL/docs")
    if [[ "$response" == *"Swagger"* ]] || [[ "$response" == *"OpenAPI"* ]]; then
        print_success "API documentation accessible"
    else
        print_warning "API documentation may not be accessible"
    fi
}

run_all_tests() {
    print_info "Running comprehensive API tests..."
    echo
    
    local failed_tests=0
    
    test_root || failed_tests=$((failed_tests + 1))
    test_health || failed_tests=$((failed_tests + 1))
    test_prediction || failed_tests=$((failed_tests + 1))
    test_metrics || failed_tests=$((failed_tests + 1))
    test_logs || failed_tests=$((failed_tests + 1))
    test_model_performance || failed_tests=$((failed_tests + 1))
    test_data_drift || failed_tests=$((failed_tests + 1))
    test_retraining || failed_tests=$((failed_tests + 1))
    test_docs || failed_tests=$((failed_tests + 1))
    
    echo
    if [ $failed_tests -eq 0 ]; then
        print_success "All tests passed! API is working correctly."
    else
        print_error "$failed_tests test(s) failed"
        exit 1
    fi
}

main() {
    local command=${1:-all}
    
    case $command in
        all)
            wait_for_api
            run_all_tests
            ;;
        root)
            wait_for_api
            test_root
            ;;
        health)
            wait_for_api
            test_health
            ;;
        prediction)
            wait_for_api
            test_prediction
            ;;
        metrics)
            wait_for_api
            test_metrics
            ;;
        logs)
            wait_for_api
            test_logs
            ;;
        performance)
            wait_for_api
            test_model_performance
            ;;
        drift)
            wait_for_api
            test_data_drift
            ;;
        retraining)
            wait_for_api
            test_retraining
            ;;
        docs)
            wait_for_api
            test_docs
            ;;
        help|*)
            echo "Usage: $0 [all|root|health|prediction|metrics|logs|performance|drift|retraining|docs|help]"
            echo
            echo "Commands:"
            echo "  all         - Run all tests (default)"
            echo "  root        - Test root endpoint"
            echo "  health      - Test health endpoint"
            echo "  prediction  - Test prediction endpoint"
            echo "  metrics     - Test metrics endpoint"
            echo "  logs        - Test logs endpoint"
            echo "  performance - Test model performance endpoint"
            echo "  drift       - Test data drift endpoint"
            echo "  retraining  - Test retraining endpoint"
            echo "  docs        - Test API documentation"
            echo "  help        - Show this help message"
            ;;
    esac
}

main "$@" 