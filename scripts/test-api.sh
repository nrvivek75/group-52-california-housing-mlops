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
API_URL="http://localhost:8001"
TIMEOUT=10

# Function to print colored output
print_status() {
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

# Function to wait for API to be ready
wait_for_api() {
    print_status "Waiting for API to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "${API_URL}/health" > /dev/null 2>&1; then
            print_success "API is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - API not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "API failed to become ready within expected time"
    return 1
}

# Function to test health endpoint
test_health() {
    print_status "Testing health endpoint..."
    
    response=$(curl -s "${API_URL}/health")
    
    if echo "$response" | grep -q "healthy"; then
        print_success "Health check passed"
        echo "Response: $response"
    else
        print_error "Health check failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test root endpoint
test_root() {
    print_status "Testing root endpoint..."
    
    response=$(curl -s "${API_URL}/")
    
    if echo "$response" | grep -q "California Housing"; then
        print_success "Root endpoint working"
        echo "Response: $response"
    else
        print_error "Root endpoint failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test prediction endpoint
test_prediction() {
    print_status "Testing prediction endpoint..."
    
    # Sample housing data
    sample_data='{
        "longitude": -122.23,
        "latitude": 37.88,
        "housing_median_age": 41.0,
        "total_rooms": 880.0,
        "total_bedrooms": 129.0,
        "population": 322.0,
        "households": 126.0,
        "median_income": 8.3252
    }'
    
    response=$(curl -s -X POST "${API_URL}/predict" \
        -H "Content-Type: application/json" \
        -d "$sample_data")
    
    if echo "$response" | grep -q "prediction"; then
        print_success "Prediction endpoint working"
        echo "Response: $response"
    else
        print_error "Prediction endpoint failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test metrics endpoint
test_metrics() {
    print_status "Testing metrics endpoint..."
    
    response=$(curl -s "${API_URL}/metrics")
    
    if echo "$response" | grep -q "total_predictions"; then
        print_success "Metrics endpoint working"
        echo "Response: $response"
    else
        print_error "Metrics endpoint failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test logs endpoint
test_logs() {
    print_status "Testing logs endpoint..."
    
    response=$(curl -s "${API_URL}/logs?limit=5")
    
    if echo "$response" | grep -q "logs"; then
        print_success "Logs endpoint working"
        echo "Response: $response"
    else
        print_error "Logs endpoint failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test model performance endpoint
test_model_performance() {
    print_status "Testing model performance endpoint..."
    
    response=$(curl -s "${API_URL}/model/performance")
    
    if echo "$response" | grep -q "performance"; then
        print_success "Model performance endpoint working"
        echo "Response: $response"
    else
        print_error "Model performance endpoint failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test data drift endpoint
test_data_drift() {
    print_status "Testing data drift endpoint..."
    
    response=$(curl -s "${API_URL}/model/drift")
    
    if echo "$response" | grep -q "drift"; then
        print_success "Data drift endpoint working"
        echo "Response: $response"
    else
        print_error "Data drift endpoint failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    print_status "Starting API tests..."
    echo ""
    
    local failed_tests=0
    
    # Test basic endpoints
    test_root || failed_tests=$((failed_tests + 1))
    echo ""
    
    test_health || failed_tests=$((failed_tests + 1))
    echo ""
    
    # Test core functionality
    test_prediction || failed_tests=$((failed_tests + 1))
    echo ""
    
    # Test monitoring endpoints
    test_metrics || failed_tests=$((failed_tests + 1))
    echo ""
    
    test_logs || failed_tests=$((failed_tests + 1))
    echo ""
    
    # Test model management endpoints
    test_model_performance || failed_tests=$((failed_tests + 1))
    echo ""
    
    test_data_drift || failed_tests=$((failed_tests + 1))
    echo ""
    
    # Summary
    if [ $failed_tests -eq 0 ]; then
        print_success "🎉 All tests passed! API is working correctly."
    else
        print_error "❌ $failed_tests test(s) failed. Please check the API logs."
        return 1
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  all       Run all tests (default)"
    echo "  health    Test health endpoint only"
    echo "  predict   Test prediction endpoint only"
    echo "  metrics   Test metrics endpoint only"
    echo "  logs      Test logs endpoint only"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Run all tests"
    echo "  $0 health       # Test health only"
    echo "  $0 predict      # Test prediction only"
}

# Main script logic
main() {
    local command=${1:-all}
    
    case $command in
        all)
            wait_for_api
            run_all_tests
            ;;
        health)
            wait_for_api
            test_health
            ;;
        predict)
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
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 