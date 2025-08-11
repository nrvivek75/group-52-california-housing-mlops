#!/bin/bash
# Quick Fix Script for Pod - Copy and paste this into your pod

echo "🔧 Quick Fix Script for MLOps Pod"
echo "=================================="

# Check current status
echo "📊 Current Status:"
echo "Working directory: $(pwd)"
echo "User: $(whoami)"
echo ""

# Check if we're in the right container
if [ ! -f "/app/src/api.py" ]; then
    echo "❌ Not in MLOps container!"
    exit 1
fi

echo "✅ Confirmed: Running in MLOps container"
echo ""

# Check MLflow runs
echo "🔍 Checking MLflow runs..."
if [ -d "/app/mlruns" ]; then
    echo "MLflow directory exists"
    ls -la /app/mlruns/
    echo ""
else
    echo "❌ MLflow directory missing!"
fi

# Check Grafana config
echo "🔍 Checking Grafana config..."
if [ -f "/app/grafana/provisioning/dashboards/dashboard.yml" ]; then
    echo "✅ Dashboard config exists"
    cat /app/grafana/provisioning/dashboards/dashboard.yml
else
    echo "❌ Dashboard config missing!"
fi

echo ""

# Try to create MLflow runs if missing
if [ ! -d "/app/mlruns" ] || [ -z "$(ls -A /app/mlruns 2>/dev/null)" ]; then
    echo "🔧 Creating MLflow runs..."
    cd /app
    python scripts/init_container.py
    echo ""
fi

# Try to fix Grafana if missing
if [ ! -f "/app/grafana/provisioning/dashboards/dashboard.yml" ]; then
    echo "🔧 Creating Grafana config..."
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
    echo "✅ Created Grafana config"
fi

echo ""
echo "🔍 Final check - MLflow runs:"
if [ -d "/app/mlruns" ]; then
    ls -la /app/mlruns/
fi

echo ""
echo "🌐 Access URLs:"
echo "API: http://localhost:8001"
echo "MLflow: http://localhost:5002"
echo "Grafana: http://localhost:3000"
echo ""
echo "✅ Quick fix completed!" 