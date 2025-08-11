#!/bin/bash
# Container Diagnostics Script for MLOps
# Comprehensive diagnostics for troubleshooting production issues

set -e

echo "🔍 Starting comprehensive container diagnostics..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check service status
check_service_status() {
    local service_name=$1
    local service_id=$2
    
    log "🔍 Checking $service_name status..."
    if supervisorctl status $service_id | grep -q "RUNNING"; then
        log "✅ $service_name is RUNNING"
        return 0
    else
        log "❌ $service_name is not running"
        supervisorctl status $service_id
        return 1
    fi
}

# Function to check service logs
check_service_logs() {
    local service_name=$1
    local log_file=$2
    local lines=${3:-20}
    
    log "📋 Checking $service_name logs (last $lines lines)..."
    if [ -f "$log_file" ]; then
        echo "--- $service_name logs ---"
        tail -n $lines "$log_file"
        echo "--- end logs ---"
    else
        log "⚠️  Log file not found: $log_file"
    fi
}

# Function to check resource usage
check_resources() {
    log "💾 Checking resource usage..."
    
    echo "Memory usage:"
    free -h
    
    echo "Disk usage:"
    df -h
    
    echo "Process count:"
    ps aux | wc -l
    
    echo "Top processes by memory:"
    ps aux --sort=-%mem | head -5
}

# Function to check network connectivity
check_network() {
    log "🌐 Checking network connectivity..."
    
    echo "Local ports in use:"
    netstat -tlnp 2>/dev/null | grep LISTEN || echo "netstat not available"
    
    echo "Container IP:"
    hostname -i 2>/dev/null || echo "hostname not available"
    
    echo "DNS resolution:"
    nslookup google.com 2>/dev/null || echo "nslookup not available"
}

# Function to check file permissions
check_permissions() {
    log "🔐 Checking file permissions..."
    
    local critical_dirs=("/app" "/app/logs" "/app/models" "/app/mlruns")
    
    for dir in "${critical_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo "Directory: $dir"
            ls -ld "$dir"
            echo "Owner: $(stat -c '%U:%G' "$dir")"
        else
            log "⚠️  Directory not found: $dir"
        fi
    done
}

# Function to check Python environment
check_python_env() {
    log "🐍 Checking Python environment..."
    
    echo "Python version:"
    python --version 2>/dev/null || echo "Python not available"
    
    echo "Python path:"
    python -c "import sys; print('\n'.join(sys.path))" 2>/dev/null || echo "Python path not available"
    
    echo "Installed packages:"
    pip list 2>/dev/null | head -10 || echo "pip not available"
}

# Function to check MLflow status
check_mlflow_status() {
    log "🔬 Checking MLflow status..."
    
    if [ -d "/app/mlruns" ]; then
        echo "MLflow directory exists: /app/mlruns"
        echo "Directory contents:"
        ls -la /app/mlruns/
        
        echo "Experiment count:"
        find /app/mlruns -name "*.yaml" | wc -l
        
        echo "Run count:"
        find /app/mlruns -type d -name "*" | grep -v "^/app/mlruns$" | wc -l
    else
        log "❌ MLflow directory not found"
    fi
}

# Function to check model availability
check_models() {
    log "🤖 Checking model availability..."
    
    if [ -d "/app/models" ]; then
        echo "Models directory exists: /app/models"
        echo "Directory contents:"
        ls -la /app/models/
        
        echo "Model files:"
        find /app/models -name "*.pkl" -o -name "conda.yaml"
        
        echo "Model count:"
        find /app/models -name "*.pkl" | wc -l
        find /app/models -name "conda.yaml" | wc -l
    else
        log "❌ Models directory not found"
    fi
}

# Function to check API health
check_api_health() {
    log "🔌 Checking API health..."
    
    if curl -s "http://localhost:8001/health" > /dev/null 2>&1; then
        echo "API health endpoint response:"
        curl -s "http://localhost:8001/health" | python -m json.tool 2>/dev/null || curl -s "http://localhost:8001/health"
    else
        log "❌ API health endpoint not accessible"
    fi
}

# Main diagnostics
log "🚀 Starting diagnostics..."

echo "=========================================="
echo "CONTAINER ENVIRONMENT"
echo "=========================================="
echo "Container ID: $(hostname)"
echo "Working directory: $(pwd)"
echo "User: $(whoami)"
echo "Shell: $SHELL"
echo "Python: $(which python 2>/dev/null || echo 'not found')"

echo ""
echo "=========================================="
echo "SERVICE STATUS"
echo "=========================================="
check_service_status "API" "api"
check_service_status "MLflow" "mlflow"
check_service_status "Prometheus" "prometheus"
check_service_status "Grafana" "grafana"

echo ""
echo "=========================================="
echo "RESOURCE USAGE"
echo "=========================================="
check_resources

echo ""
echo "=========================================="
echo "NETWORK STATUS"
echo "=========================================="
check_network

echo ""
echo "=========================================="
echo "FILE PERMISSIONS"
echo "=========================================="
check_permissions

echo ""
echo "=========================================="
echo "PYTHON ENVIRONMENT"
echo "=========================================="
check_python_env

echo ""
echo "=========================================="
echo "MLFLOW STATUS"
echo "=========================================="
check_mlflow_status

echo ""
echo "=========================================="
echo "MODEL AVAILABILITY"
echo "=========================================="
check_models

echo ""
echo "=========================================="
echo "API HEALTH"
echo "=========================================="
check_api_health

echo ""
echo "=========================================="
echo "SERVICE LOGS"
echo "=========================================="
check_service_logs "API" "/var/log/supervisor/api.err.log"
check_service_logs "MLflow" "/var/log/supervisor/mlflow.err.log"
check_service_logs "Prometheus" "/var/log/supervisor/prometheus.err.log"
check_service_logs "Grafana" "/var/log/supervisor/grafana.err.log"

echo ""
echo "=========================================="
echo "DIAGNOSTICS COMPLETED"
echo "=========================================="
log "🎯 Diagnostics completed. Check the output above for any issues."
log "💡 Use 'supervisorctl restart <service>' to restart failed services."
log "📋 Check individual log files for detailed error information." 