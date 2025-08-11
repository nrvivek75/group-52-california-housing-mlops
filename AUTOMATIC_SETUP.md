 # Automatic MLOps Setup Guide

## Overview

This MLOps container is designed to **automatically start everything** when the pod/container is created. No manual intervention is required.

## What Happens Automatically

### 1. Container Startup Sequence

When the container starts, this is the automatic sequence:

```
1. Supervisor starts
2. Startup script runs (one-time initialization)
3. All services start in parallel:
   - FastAPI API (port 8001)
   - MLflow UI (port 5002)
   - Prometheus (port 9090)
   - Grafana (port 3000)
4. Services become available automatically
```

### 2. Automatic Initialization

The startup script (`scripts/startup.sh`) automatically:

- ✅ **Creates necessary directories**
- ✅ **Copies trained models** (if they exist)
- ✅ **Copies MLflow data** (if it exists)
- ✅ **Trains models** (if none exist)
- ✅ **Initializes MLflow experiment**
- ✅ **Tests all services**
- ✅ **Generates initial metrics**
- ✅ **Exits successfully**

### 3. Service Dependencies

```
Startup Script → API → MLflow → Prometheus → Grafana
     ↓              ↓       ↓         ↓         ↓
  Initialize    Model    UI Ready   Scraping  Dashboards
  Everything    Loading  (Runs)     Metrics   Available
```

## Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Single Docker Container                  │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────┐ │
│  │   FastAPI   │ │   MLflow    │ │ Prometheus  │ │Grafana│ │
│  │   (8001)    │ │   (5002)    │ │   (9090)    │ │(3000) │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────┘ │
│                                                             │
│  Supervisor manages all services                           │
│  Startup script initializes everything                     │
│  All services share the same filesystem                     │
└─────────────────────────────────────────────────────────────┘
```

## Automatic Features

### 🚀 **Zero Manual Setup**
- Container starts everything automatically
- Models are loaded automatically
- MLflow shows training runs automatically
- Grafana dashboards appear automatically
- Metrics are collected automatically

### 📊 **Automatic Data Population**
- Training runs are visible in MLflow
- API metrics are collected by Prometheus
- Grafana dashboards show real-time data
- No manual data entry required

### 🔄 **Automatic Retraining**
- Retraining system is available via API
- Performance monitoring triggers retraining
- Data drift detection triggers retraining
- Scheduled retraining available

## Service Access Points

Once the container is running, all services are automatically available at:

| Service | URL | Purpose |
|---------|-----|---------|
| **FastAPI** | http://localhost:8001 | Housing price predictions |
| **MLflow** | http://localhost:5002 | Experiment tracking & models |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **Grafana** | http://localhost:3000 | Monitoring dashboards |

**Grafana Login**: `admin` / `admin`

## What You'll See Automatically

### 1. **MLflow UI** (http://localhost:5002)
- ✅ Experiment: "california_housing_experiment"
- ✅ Multiple training runs with different models
- ✅ Best model: Gradient Boosting (RMSE: ~48,170)
- ✅ Model registry with versions

### 2. **Grafana Dashboards** (http://localhost:3000)
- ✅ API Request Rate
- ✅ API Response Time
- ✅ Total Predictions
- ✅ Health Check Requests
- ✅ Error Rate
- ✅ Model Performance Metrics

### 3. **FastAPI API** (http://localhost:8001)
- ✅ Health endpoint working
- ✅ Model loaded and ready
- ✅ Prediction endpoint functional
- ✅ Metrics endpoint available
- ✅ Retraining triggers available

### 4. **Prometheus** (http://localhost:9090)
- ✅ API metrics being scraped
- ✅ MLflow metrics available
- ✅ Self-monitoring active

## Testing Everything

To verify all services are working automatically:

```bash
# Test all services
python scripts/test_services.py

# Test individual endpoints
curl http://localhost:8001/health
curl http://localhost:8001/metrics
curl http://localhost:5002
curl http://localhost:9090/api/v1/targets
curl http://localhost:3000
```

## Troubleshooting

### If MLflow Shows No Runs
1. Check container logs: `docker logs <container_name>`
2. Verify startup script completed successfully
3. Check if models were trained: `ls -la /app/mlruns/`

### If Grafana Shows No Dashboards
1. Wait for initial metrics to be generated
2. Check Prometheus targets are healthy
3. Verify Grafana data source is connected

### If API Model Not Loaded
1. Check startup script logs
2. Verify models exist in `/app/models/`
3. Check API logs for model loading errors

## Container Lifecycle

```
Pod Created → Container Starts → Supervisor Starts → Startup Script Runs → Services Start → Everything Ready
     ↓              ↓                ↓                ↓              ↓           ↓
  Kubernetes    Docker Image    Process Mgmt    Initialize    API/MLflow/   Full MLOps
  Orchestrates  Downloads      Starts          Data/Models   Prometheus/   Stack Ready
                                                              Grafana
```

## Benefits of This Approach

1. **🎯 Zero Manual Setup**: Everything works out of the box
2. **🚀 Fast Deployment**: Single container with all services
3. **📊 Rich Data**: Pre-populated with training runs and metrics
4. **🔍 Full Monitoring**: Complete observability stack
5. **🔄 Production Ready**: Retraining, monitoring, and alerting
6. **📈 Scalable**: Easy to deploy to multiple environments

## Next Steps

Once the container is running:

1. **Explore MLflow**: View training runs and models
2. **Check Grafana**: Monitor API performance and metrics
3. **Test API**: Make predictions and see metrics update
4. **Customize**: Modify dashboards or add new metrics
5. **Scale**: Deploy to production or other environments

## Support

If you encounter issues:

1. Check container logs: `docker logs <container_name>`
2. Run the test script: `python scripts/test_services.py`
3. Verify all services are responding
4. Check startup script completion

The system is designed to be completely self-contained and automatic. Everything should work without manual intervention!