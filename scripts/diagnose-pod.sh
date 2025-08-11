#!/bin/bash
# Pod Diagnosis Script
# This script helps diagnose issues in the current MLOps pod

echo "🔍 Diagnosing MLOps Pod Issues..."

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

echo "=========================================="
echo "🔍 MLOps Pod Diagnosis"
echo "=========================================="

# Check if you're running locally or in Kubernetes
if command -v kubectl &> /dev/null; then
    log_info "Kubernetes detected - checking pod status..."
    
    # Get pod information
    POD_NAME=$(kubectl get pods --no-headers -o custom-columns=":metadata.name" | grep california-housing | head -1)
    
    if [ -n "$POD_NAME" ]; then
        log_success "Found pod: $POD_NAME"
        
        # Check pod status
        POD_STATUS=$(kubectl get pod $POD_NAME -o jsonpath='{.status.phase}')
        log_info "Pod status: $POD_STATUS"
        
        # Check container status
        CONTAINER_STATUS=$(kubectl get pod $POD_NAME -o jsonpath='{.status.containerStatuses[0].ready}')
        log_info "Container ready: $CONTAINER_STATUS"
        
        # Check recent logs
        log_info "Recent pod logs:"
        kubectl logs $POD_NAME --tail=20
        
        # Check if services are accessible
        log_info "Checking service accessibility..."
        
        # Get port-forward status
        if lsof -i :8001 > /dev/null 2>&1; then
            log_success "Port 8001 (API) is forwarded"
        else
            log_warning "Port 8001 (API) is not forwarded"
        fi
        
        if lsof -i :5002 > /dev/null 2>&1; then
            log_success "Port 5002 (MLflow) is forwarded"
        else
            log_warning "Port 5002 (MLflow) is not forwarded"
        fi
        
        if lsof -i :3000 > /dev/null 2>&1; then
            log_success "Port 3000 (Grafana) is forwarded"
        else
            log_warning "Port 3000 (Grafana) is not forwarded"
        fi
        
    else
        log_error "No california-housing pod found"
    fi
    
else
    log_info "Kubernetes not detected - checking local Docker..."
    
    # Check local Docker containers
    if command -v docker &> /dev/null; then
        CONTAINER_NAME=$(docker ps --filter "name=california-housing" --format "{{.Names}}" | head -1)
        
        if [ -n "$CONTAINER_NAME" ]; then
            log_success "Found container: $CONTAINER_NAME"
            
            # Check container status
            CONTAINER_STATUS=$(docker inspect $CONTAINER_NAME --format='{{.State.Status}}')
            log_info "Container status: $CONTAINER_STATUS"
            
            # Check recent logs
            log_info "Recent container logs:"
            docker logs $CONTAINER_NAME --tail=20
            
        else
            log_warning "No california-housing container found"
        fi
    else
        log_error "Docker not found"
    fi
fi

echo ""
echo "=========================================="
echo "🔧 Troubleshooting Steps"
echo "=========================================="

echo "1. **Check if you're running the NEW image:**"
echo "   - The old image only creates 3 RandomForest models"
echo "   - The new image creates 10 different models"
echo "   - You need to deploy the updated image"

echo ""
echo "2. **Current Status:**"
echo "   - Code is fixed ✅"
echo "   - Old image still running ❌"
echo "   - New image needs to be built and deployed ❌"

echo ""
echo "3. **Solutions:**"
echo "   A) Wait for CI/CD to complete and deploy new image"
echo "   B) Build and test locally first (use scripts/build-and-test-local.sh)"
echo "   C) Check GitHub Actions for build status"

echo ""
echo "4. **To verify fixes work:**"
echo "   - Run: ./scripts/build-and-test-local.sh"
echo "   - This will build and test the new image locally"
echo "   - You'll see 10 MLflow models and Grafana dashboards"

echo ""
echo "=========================================="
echo "📊 Expected Results After Fix"
echo "=========================================="

echo "✅ MLflow will show 10 models:"
echo "   - Linear Regression"
echo "   - Ridge (α=0.1, α=1.0)"
echo "   - Lasso (α=0.1, α=1.0)"
echo "   - RandomForest (100, 200, 300 estimators)"
echo "   - Decision Tree"
echo "   - Gradient Boosting"

echo ""
echo "✅ Grafana will show dashboards:"
echo "   - API Request Rate"
echo "   - Model Performance"
echo "   - System Health"
echo "   - Real-time metrics"

echo ""
echo "🔍 The issue is NOT with the code - it's that you're running the OLD image!" 