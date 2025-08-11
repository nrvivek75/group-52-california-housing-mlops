#!/bin/bash

echo "🔧 Fixing Grafana Issues..."
echo "============================"

# Check if we're in the right container
if [ ! -f "/app/src/api.py" ]; then
    echo "❌ Not in MLOps container!"
    exit 1
fi

echo "✅ Confirmed: Running in MLOps container"
echo ""

# Check Grafana status
echo "🔍 Checking Grafana status..."
if curl -s "http://localhost:3000/api/health" > /dev/null; then
    echo "✅ Grafana is running"
else
    echo "❌ Grafana is not responding"
    exit 1
fi

# Check Prometheus connection
echo "🔍 Checking Prometheus connection..."
if curl -s "http://localhost:9090/api/v1/query?query=up" > /dev/null; then
    echo "✅ Prometheus is responding"
else
    echo "❌ Prometheus is not responding"
    exit 1
fi

# Check datasource
echo "🔍 Checking Grafana datasource..."
if curl -s -u "admin:admin" "http://localhost:3000/api/datasources" | grep -q "Prometheus"; then
    echo "✅ Prometheus datasource exists"
else
    echo "⚠️  Prometheus datasource not found, creating it..."
    
    # Create Prometheus datasource
    curl -s -X POST -u "admin:admin" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://localhost:9090",
            "access": "proxy",
            "isDefault": true
        }' \
        "http://localhost:3000/api/datasources"
    
    echo "✅ Prometheus datasource created"
fi

# Check dashboards
echo "🔍 Checking dashboards..."
dashboards=$(curl -s -u "admin:admin" "http://localhost:3000/api/search?type=dash-db")
if [ $? -eq 0 ]; then
    dashboard_count=$(echo "$dashboards" | jq '. | length' 2>/dev/null || echo "0")
    echo "✅ Found $dashboard_count dashboards"
else
    echo "⚠️  Could not check dashboards"
fi

# Create a simple dashboard if none exist
if [ "$dashboard_count" = "0" ] || [ "$dashboard_count" = "" ]; then
    echo "🔧 Creating simple dashboard..."
    
    # Create a basic dashboard
    curl -s -X POST -u "admin:admin" \
        -H "Content-Type: application/json" \
        -d '{
            "dashboard": {
                "title": "MLOps Simple Dashboard",
                "panels": [
                    {
                        "title": "API Health",
                        "type": "stat",
                        "targets": [{"expr": "up{job=\"api\"}"}],
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                    },
                    {
                        "title": "Total Predictions",
                        "type": "stat",
                        "targets": [{"expr": "model_predictions_total"}],
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "30s"
            }
        }' \
        "http://localhost:3000/api/dashboards/db"
    
    echo "✅ Simple dashboard created"
fi

# Test metrics
echo "🔍 Testing metrics collection..."
if curl -s "http://localhost:8001/metrics" | grep -q "model_predictions_total"; then
    echo "✅ API metrics are being collected"
else
    echo "⚠️  API metrics not found"
fi

echo ""
echo "🌐 Access URLs:"
echo "Grafana: http://localhost:3000 (admin/admin)"
echo "Prometheus: http://localhost:9090"
echo "API: http://localhost:8001"
echo ""
echo "✅ Grafana fix completed!"
echo ""
echo "📋 Manual steps if issues persist:"
echo "1. Open Grafana: http://localhost:3000"
echo "2. Login: admin/admin"
echo "3. Go to Configuration > Data Sources"
echo "4. Add Prometheus: http://localhost:9090"
echo "5. Go to + > Import and paste dashboard JSON" 