#!/bin/bash
# Fixed Startup Script for MLOps Container
# This script ensures MLflow models are created automatically on container startup

set -e

echo "🚀 Starting MLOps Container Initialization..."
echo "=============================================="

# Function to log messages
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1"
}

log_warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1"
}

# Change to app directory
cd /app
log_info "Working directory: $(pwd)"

# Wait for MLflow service to be ready
log_info "Waiting for MLflow service to be ready..."
for i in {1..30}; do
    if curl -s "http://localhost:5002" > /dev/null 2>&1; then
        log_success "MLflow service is ready!"
        break
    fi
    log_info "Waiting for MLflow... attempt $i/30"
    sleep 2
done

# Check if MLflow runs already exist
log_info "Checking existing MLflow runs..."
if [ -d "/app/mlruns" ]; then
    RUN_COUNT=$(find /app/mlruns -name '*.yaml' 2>/dev/null | wc -l)
    log_info "Found $RUN_COUNT existing MLflow runs"
    
    if [ "$RUN_COUNT" -lt 5 ]; then
        log_warning "Only $RUN_COUNT runs found, need to create more..."
        NEED_TRAINING=true
    else
        log_success "Sufficient MLflow runs exist ($RUN_COUNT)"
        NEED_TRAINING=false
    fi
else
    log_info "No MLflow runs directory found, need to create runs..."
    NEED_TRAINING=true
fi

# Run initialization if needed
if [ "$NEED_TRAINING" = true ]; then
    log_info "Running MLflow initialization..."
    
    if [ -f "/app/scripts/init_container.py" ]; then
        log_info "Executing init_container.py..."
        python scripts/init_container.py
        
        # Wait a moment for MLflow to process the runs
        sleep 5
        
        # Verify the runs were created
        NEW_RUN_COUNT=$(find /app/mlruns -name '*.yaml' 2>/dev/null | wc -l)
        log_info "After initialization: $NEW_RUN_COUNT runs found"
        
        if [ "$NEW_RUN_COUNT" -ge 5 ]; then
            log_success "MLflow initialization completed successfully!"
        else
            log_error "MLflow initialization may have failed - only $NEW_RUN_COUNT runs found"
        fi
    else
        log_error "init_container.py not found!"
        exit 1
    fi
else
    log_success "MLflow already properly initialized"
fi

# Final verification
log_info "Performing final MLflow verification..."
if command -v python &> /dev/null; then
    python -c "
import mlflow
from mlflow.tracking import MlflowClient

try:
    mlflow.set_tracking_uri('file:./mlruns')
    experiment = mlflow.get_experiment_by_name('california_housing_experiment')
    
    if experiment:
        client = MlflowClient()
        runs = client.search_runs(experiment_ids=[experiment.experiment_id])
        print(f'✅ Final verification: {len(runs)} MLflow runs found')
        
        if len(runs) >= 5:
            print('🎉 MLflow is properly initialized with sufficient models!')
            print('Models found:')
            for i, run in enumerate(runs[:10]):
                print(f'  {i+1}. {run.info.run_name}')
        else:
            print(f'⚠️  Only {len(runs)} runs found, may need more training')
    else:
        print('❌ MLflow experiment not found')
        
except Exception as e:
    print(f'❌ MLflow verification failed: {e}')
"
else
    log_error "Python not available for verification"
fi

log_success "Startup process completed successfully!"
echo "=============================================="

# Keep the script running for a bit to ensure everything is stable
log_info "Waiting for services to stabilize..."
sleep 10

log_success "Startup process finished - container is ready!" 