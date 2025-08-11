#!/bin/bash
# Fix Inside Pod Script
# Run this script INSIDE the MLOps container to diagnose and fix issues

set -e

echo "🔧 Running MLOps Container Fix Script..."
echo "=========================================="

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

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    if curl -s "$url" > /dev/null 2>&1; then
        log_success "$service_name is running on port $port"
        return 0
    else
        log_error "$service_name is NOT running on port $port"
        return 1
    fi
}

# Function to check directory contents
check_directory() {
    local dir_path=$1
    local description=$2
    
    if [ -d "$dir_path" ]; then
        log_info "$description: $dir_path"
        echo "Contents:"
        ls -la "$dir_path" | head -10
        echo ""
    else
        log_error "$description directory not found: $dir_path"
    fi
}

echo "=========================================="
echo "🔍 Step 1: System Diagnosis"
echo "=========================================="

# Check current directory
log_info "Current working directory: $(pwd)"
log_info "Current user: $(whoami)"

# Check if we're in the right container
if [ ! -f "/app/src/api.py" ]; then
    log_error "This doesn't look like the MLOps container!"
    log_error "Expected /app/src/api.py to exist"
    exit 1
fi

log_success "Confirmed: Running in MLOps container"

# Check available disk space
log_info "Disk space:"
df -h /app

# Check available memory
log_info "Memory usage:"
free -h

echo ""
echo "=========================================="
echo "🔍 Step 2: Service Status Check"
echo "=========================================="

# Check if services are running
check_service "API" "8001" "http://localhost:8001/health"
check_service "MLflow" "5002" "http://localhost:5002"
check_service "Prometheus" "9090" "http://localhost:9090/api/v1/targets"
check_service "Grafana" "3000" "http://localhost:3000"

echo ""
echo "=========================================="
echo "🔍 Step 3: Directory Structure Check"
echo "=========================================="

# Check key directories
check_directory "/app" "App root"
check_directory "/app/src" "Source code"
check_directory "/app/scripts" "Scripts"
check_directory "/app/configs" "Configs"
check_directory "/app/data" "Data"
check_directory "/app/models" "Models"
check_directory "/app/mlruns" "MLflow runs"
check_directory "/app/logs" "Logs"
check_directory "/app/grafana" "Grafana"
check_directory "/app/grafana/provisioning/dashboards" "Grafana dashboards"
check_directory "/app/grafana/provisioning/datasources" "Grafana datasources"

echo ""
echo "=========================================="
echo "🔍 Step 4: MLflow Status Check"
echo "=========================================="

# Check MLflow experiment and runs
if command -v python &> /dev/null; then
    log_info "Checking MLflow status..."
    
    # Create a simple Python script to check MLflow
    cat > /tmp/check_mlflow.py << 'EOF'
import os
import sys
sys.path.append('/app')

try:
    import mlflow
    from mlflow.tracking import MlflowClient
    
    # Set tracking URI
    mlflow.set_tracking_uri('file:./mlruns')
    
    # Get experiment
    experiment_name = 'california_housing_experiment'
    experiment = mlflow.get_experiment_by_name(experiment_name)
    
    if experiment:
        print(f"✅ Experiment found: {experiment_name}")
        print(f"   Experiment ID: {experiment.experiment_id}")
        
        # Get runs
        client = MlflowClient()
        runs = client.search_runs(experiment_ids=[experiment.experiment_id])
        print(f"   Number of runs: {len(runs)}")
        
        if runs:
            print("   Recent runs:")
            for i, run in enumerate(runs[:5]):  # Show first 5 runs
                print(f"     {i+1}. {run.info.run_name} - Status: {run.info.status}")
        else:
            print("   ❌ No runs found!")
    else:
        print(f"❌ Experiment not found: {experiment_name}")
        
except Exception as e:
    print(f"❌ Error checking MLflow: {e}")
EOF

    python /tmp/check_mlflow.py
    rm /tmp/check_mlflow.py
    
else
    log_error "Python not available"
fi

echo ""
echo "=========================================="
echo "🔍 Step 5: Grafana Status Check"
echo "=========================================="

# Check Grafana configuration
if [ -f "/app/grafana/provisioning/dashboards/dashboard.yml" ]; then
    log_info "Grafana dashboard provisioning file found:"
    cat /app/grafana/provisioning/dashboards/dashboard.yml
else
    log_error "Grafana dashboard provisioning file not found!"
fi

if [ -f "/app/grafana/provisioning/datasources/datasource.yml" ]; then
    log_info "Grafana datasource provisioning file found:"
    cat /app/grafana/provisioning/datasources/datasource.yml
else
    log_error "Grafana datasource provisioning file not found!"
fi

echo ""
echo "=========================================="
echo "🔧 Step 6: Attempting Fixes"
echo "=========================================="

# Try to fix MLflow if no runs exist
if [ ! -d "/app/mlruns" ] || [ -z "$(ls -A /app/mlruns 2>/dev/null)" ]; then
    log_warning "No MLflow runs found, attempting to create them..."
    
    if [ -f "/app/scripts/init_container.py" ]; then
        log_info "Running init_container.py to create runs..."
        cd /app
        python scripts/init_container.py
    else
        log_error "init_container.py not found!"
    fi
fi

# Try to fix Grafana if no dashboards
if [ ! -f "/app/grafana/provisioning/dashboards/dashboard.yml" ]; then
    log_warning "Grafana dashboard provisioning missing, creating basic config..."
    
    mkdir -p /app/grafana/provisioning/dashboards
    cat > /app/grafana/provisioning/dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /app/grafana/provisioning/dashboards
EOF
    log_success "Created basic Grafana dashboard provisioning"
fi

echo ""
echo "=========================================="
echo "🔍 Step 7: Final Status Check"
echo "=========================================="

# Wait a moment for any fixes to take effect
sleep 5

# Check services again
echo "Re-checking services after fixes:"
check_service "API" "8001" "http://localhost:8001/health"
check_service "MLflow" "5002" "http://localhost:5002"
check_service "Prometheus" "9090" "http://localhost:9090/api/v1/targets"
check_service "Grafana" "3000" "http://localhost:3000"

echo ""
echo "=========================================="
echo "📋 Summary & Next Steps"
echo "=========================================="

echo "✅ What this script checked:"
echo "   - Container environment"
echo "   - Service status"
echo "   - Directory structure"
echo "   - MLflow runs"
echo "   - Grafana configuration"
echo "   - Attempted basic fixes"

echo ""
echo "🔧 If issues persist:"
echo "   1. Check the logs above for specific errors"
echo "   2. The container may need to be rebuilt with the latest code"
echo "   3. Run this script again after any manual fixes"

echo ""
echo "🌐 Access URLs:"
echo "   - API: http://localhost:8001"
echo "   - MLflow: http://localhost:5002"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin/admin)"

echo ""
log_success "Container diagnosis and fix attempt completed!" 