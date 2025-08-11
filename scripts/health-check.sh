#!/bin/bash
# Health Check Script for MLOps Container
# Performs comprehensive health checks on all services

set -e

echo "🏥 Starting comprehensive health check..."

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo "🔍 Checking $service_name..."
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✅ $service_name is healthy"
        return 0
    else
        echo "❌ $service_name is unhealthy"
        return 1
    fi
}

# Function to check directory structure
check_directory() {
    local dir_name=$1
    local dir_path=$2
    
    echo "📁 Checking $dir_name..."
    if [ -d "$dir_path" ]; then
        echo "✅ $dir_name exists: $dir_path"
        return 0
    else
        echo "❌ $dir_name missing: $dir_path"
        return 1
    fi
}

# Function to check file existence
check_file() {
    local file_name=$1
    local file_path=$2
    
    echo "📄 Checking $file_name..."
    if [ -f "$file_path" ]; then
        echo "✅ $file_name exists: $file_path"
        return 0
    else
        echo "❌ $file_name missing: $file_path"
        return 1
    fi
}

# Initialize health status
overall_health=0

echo "🚀 Checking container environment..."
echo "   Working directory: $(pwd)"
echo "   User: $(whoami)"
echo "   Python version: $(python --version 2>/dev/null || echo 'Python not available')"

# Check essential directories
echo ""
echo "📂 Checking directory structure..."
check_directory "logs" "/app/logs" || overall_health=1
check_directory "models" "/app/models" || overall_health=1
check_directory "data" "/app/data" || overall_health=1
check_directory "mlruns" "/app/mlruns" || overall_health=1

# Check essential files
echo ""
echo "📄 Checking essential files..."
check_file "API" "/app/src/api.py" || overall_health=1
check_file "training script" "/app/scripts/train_models.py" || overall_health=1
check_file "startup script" "/app/scripts/startup.sh" || overall_health=1

# Check service health
echo ""
echo "🌐 Checking service health..."
check_service "API" "http://localhost:8001/health" || overall_health=1
check_service "MLflow" "http://localhost:5002" || overall_health=1
check_service "Prometheus" "http://localhost:9090/-/healthy" || overall_health=1
check_service "Grafana" "http://localhost:3000/api/health" || overall_health=1

# Check MLflow runs
echo ""
echo "🔬 Checking MLflow runs..."
if [ -d "/app/mlruns" ]; then
    run_count=$(find /app/mlruns -name "*.yaml" 2>/dev/null | wc -l)
    echo "📊 Found $run_count MLflow runs"
    
    if [ $run_count -ge 3 ]; then
        echo "✅ Sufficient MLflow runs found (need 3, have $run_count)"
    else
        echo "⚠️  Insufficient MLflow runs (need 3, have $run_count)"
        overall_health=1
    fi
else
    echo "❌ No MLflow directory found"
    overall_health=1
fi

# Check model availability
echo ""
echo "🤖 Checking model availability..."
if [ -d "/app/models" ]; then
    model_files=$(find /app/models -name "*.pkl" -o -name "conda.yaml" | wc -l)
    echo "📊 Found $model_files model files"
    
    if [ $model_files -gt 0 ]; then
        echo "✅ Models found in models directory"
    else
        echo "⚠️  No models found in models directory"
        overall_health=1
    fi
else
    echo "❌ Models directory not found"
    overall_health=1
fi

# Check API model loading
echo ""
echo "🔌 Testing API model loading..."
if curl -s "http://localhost:8001/health" | grep -q '"model_loaded":true'; then
    echo "✅ API model is loaded and ready"
else
    echo "⚠️  API model is not loaded"
    overall_health=1
fi

# Final health assessment
echo ""
echo "🏁 Health check completed!"
if [ $overall_health -eq 0 ]; then
    echo "🎉 All systems are healthy!"
    echo ""
    echo "📋 Service Summary:"
    echo "   API: http://localhost:8001"
    echo "   MLflow: http://localhost:5002"
    echo "   Prometheus: http://localhost:9090"
    echo "   Grafana: http://localhost:3000"
    exit 0
else
    echo "⚠️  Some issues detected. Check the logs above."
    echo ""
    echo "🔧 Troubleshooting commands:"
    echo "   # Check container logs"
    echo "   docker logs <container_name>"
    echo "   # Restart services"
    echo "   supervisorctl restart all"
    echo "   # Check MLflow status"
    echo "   python scripts/init_container.py"
    exit 1
fi 