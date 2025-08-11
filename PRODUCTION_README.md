# California Housing MLOps - Production Deployment Guide

## 🏗️ **Production Architecture**

This MLOps platform provides a production-ready machine learning service with:
- **FastAPI API** for housing price predictions
- **MLflow** for experiment tracking and model management
- **Prometheus** for metrics collection
- **Grafana** for monitoring dashboards
- **Automated CI/CD** with GitHub Actions

## 📁 **Production File Structure**

```
california-housing-mlops/
├── src/                          # Core application code
│   ├── api.py                   # FastAPI application
│   ├── retraining.py            # Model retraining system
│   └── utils/                   # Utility modules
│       ├── config.py            # Configuration management
│       └── mlflow_utils.py      # MLflow utilities
├── scripts/                      # Production scripts
│   ├── train_models.py          # Model training pipeline
│   ├── model-loader.py          # Model loading and validation
│   ├── health-check.sh          # Comprehensive health checks
│   ├── container-diagnostics.sh # Container troubleshooting
│   ├── training-validator.py    # Training result validation
│   ├── deploy-production.sh     # Production deployment
│   └── startup.sh               # Container initialization
├── tests/                        # Test suite
├── grafana/                      # Monitoring dashboards
├── .github/workflows/            # CI/CD pipelines
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local development
├── supervisord.conf             # Process management
└── requirements.txt              # Dependencies
```

## 🚀 **Quick Start (Production)**

### 1. **Deploy with Production Script**

```bash
# Clone repository
git clone <repository-url>
cd california-housing-mlops

# Make scripts executable
chmod +x scripts/*.sh

# Deploy to production
./scripts/deploy-production.sh deploy

# Check status
./scripts/deploy-production.sh status

# View logs
./scripts/deploy-production.sh logs
```

### 2. **Manual Deployment**

```bash
# Build and run
docker build -t california-housing-mlops:latest .
docker run -d \
  --name california-housing-mlops-prod \
  -p 8001:8001 -p 5002:5002 -p 9090:9090 -p 3000:3000 \
  california-housing-mlops:latest
```

## 🔧 **Production Scripts**

### **Core Operations**
- **`deploy-production.sh`** - Production deployment with validation
- **`health-check.sh`** - Comprehensive service health monitoring
- **`container-diagnostics.sh`** - Troubleshooting and diagnostics

### **ML Operations**
- **`train_models.py`** - Train 3 essential models (Linear, Decision Tree, Random Forest)
- **`model-loader.py`** - Load and validate models for production
- **`training-validator.py`** - Validate training results and model quality

### **Container Management**
- **`startup.sh`** - Container initialization and service startup
- **`deploy-production.sh`** - Production deployment with rollback

## 📊 **Service Endpoints**

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **API** | 8001 | http://localhost:8001 | Housing price predictions |
| **MLflow** | 5002 | http://localhost:5002 | Experiment tracking |
| **Prometheus** | 9090 | http://localhost:9090 | Metrics collection |
| **Grafana** | 3000 | http://localhost:3000 | Monitoring dashboards |

## 🧪 **Testing & Validation**

### **Run Health Checks**
```bash
# Comprehensive health check
./scripts/health-check.sh

# Container diagnostics
./scripts/container-diagnostics.sh

# Training validation
python scripts/training-validator.py
```

### **Test API Endpoints**
```bash
# Health check
curl http://localhost:8001/health

# Make prediction
curl -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "longitude": -122.25,
    "latitude": 37.85,
    "housing_median_age": 25.0,
    "total_rooms": 2000.0,
    "total_bedrooms": 300.0,
    "population": 800.0,
    "households": 250.0,
    "median_income": 8.5
  }'
```

## 🔍 **Monitoring & Observability**

### **Prometheus Metrics**
- Model prediction counts and latency
- API request rates and response times
- System resource usage

### **Grafana Dashboards**
- **MLOps Overview** - Service health and performance
- **Model Performance** - RMSE and R² metrics
- **System Monitoring** - CPU, memory, and network

### **Logs**
- Application logs: `/app/logs/api.log`
- Training logs: `/app/logs/training.log`
- Supervisor logs: `/var/log/supervisor/`

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Model Not Loading**
   ```bash
   # Check model files
   ./scripts/container-diagnostics.sh
   
   # Reload models
   python scripts/model-loader.py
   ```

2. **Services Not Starting**
   ```bash
   # Check service status
   supervisorctl status
   
   # Restart services
   supervisorctl restart all
   ```

3. **Training Failures**
   ```bash
   # Validate training results
   python scripts/training-validator.py
   
   # Check MLflow runs
   curl http://localhost:5002
   ```

### **Debug Commands**
```bash
# Container diagnostics
./scripts/container-diagnostics.sh

# Health check
./scripts/health-check.sh

# View logs
docker logs <container-name>

# Access container
docker exec -it <container-name> /bin/bash
```

## 🔄 **CI/CD Pipeline**

### **GitHub Actions**
- **Lint & Test** - Code quality and testing
- **Build & Push** - Docker image creation and deployment
- **Automated Testing** - Validation on every push

### **Deployment Process**
1. Code pushed to `main` branch
2. Automated testing and validation
3. Docker image built and pushed to registry
4. Production deployment with health checks
5. Rollback on failure

## 📈 **Scaling & Performance**

### **Resource Requirements**
- **Memory**: 2GB minimum, 4GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Storage**: 10GB minimum for models and data

### **Performance Tuning**
- Model caching for faster predictions
- Batch prediction endpoints
- Async processing for retraining
- Resource limits and monitoring

## 🔒 **Security Considerations**

### **Production Hardening**
- Environment variable configuration
- Network isolation with Docker networks
- Volume encryption for sensitive data
- Regular security updates
- Access control and authentication

### **Monitoring & Alerting**
- Service health monitoring
- Performance metrics tracking
- Error rate monitoring
- Resource usage alerts

## 📚 **Additional Resources**

- **API Documentation**: http://localhost:8001/docs
- **MLflow UI**: http://localhost:5002
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## 🆘 **Support**

For production issues:
1. Check health status: `./scripts/health-check.sh`
2. Run diagnostics: `./scripts/container-diagnostics.sh`
3. Review logs: `docker logs <container-name>`
4. Validate training: `python scripts/training-validator.py`

---

**Production Status**: ✅ Ready for Production Deployment
**Last Updated**: $(date)
**Version**: 2.0.0 