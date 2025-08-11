# 🚀 Local Deployment Guide for California Housing MLOps

This guide will walk you through getting your MLOps project up and running locally after the CI/CD pipeline completes and pushes the Docker image.

## 📋 Prerequisites

- Docker installed and running
- Ports 8001, 5002, 9090, 3000 available
- Git repository cloned locally

## 🚀 Step-by-Step Local Deployment

### 1. Pull the Latest Docker Image

```bash
# Pull the image that was just built and pushed
docker pull YOUR_DOCKER_USERNAME/california-housing-mlops:latest
```

**⚠️ Important**: Replace `YOUR_DOCKER_USERNAME` with your actual Docker Hub username.

### 2. Choose Your Deployment Method

#### Option A: Use the Convenient Script (Recommended)

```bash
# Make the script executable (if not already)
chmod +x scripts/deploy-local.sh

# Start everything
./scripts/deploy-local.sh start

# Check status
./scripts/deploy-local.sh status

# View logs
./scripts/deploy-local.sh logs
```

#### Option B: Use Docker Compose (Full Stack)

```bash
# Start all services (API + MLflow + Prometheus + Grafana)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option C: Manual Docker Commands

```bash
# Run just the API container
docker run -d \
  --name california-housing-api \
  -p 8001:8001 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/mlruns:/app/mlruns \
  YOUR_DOCKER_USERNAME/california-housing-mlops:latest
```

### 3. Test Everything is Working

#### Test the API Endpoints

```bash
# Make the test script executable
chmod +x scripts/test-api.sh

# Run all tests
./scripts/test-api.sh all

# Or test individual endpoints
./scripts/test-api.sh health
./scripts/test-api.sh predict
./scripts/test-api.sh metrics
```

#### Manual Testing

```bash
# Health check
curl http://localhost:8001/health

# Make a prediction
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "longitude": -122.23,
    "latitude": 37.88,
    "housing_median_age": 41.0,
    "total_rooms": 880.0,
    "total_bedrooms": 129.0,
    "population": 322.0,
    "households": 126.0,
    "median_income": 8.3252
  }'
```

### 4. Access All Services

| Service | URL | Purpose |
|---------|-----|---------|
| **API** | http://localhost:8001 | Main prediction API |
| **API Docs** | http://localhost:8001/docs | Interactive API documentation |
| **MLflow UI** | http://localhost:5002 | Model tracking and experiments |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **Grafana** | http://localhost:3000 | Dashboards (admin/admin) |

### 5. Verify Everything is Working

#### Check Container Status

```bash
docker ps
# Should show your containers running
```

#### Check API Health

```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy", "model_loaded": true}
```

#### Check Metrics

```bash
curl http://localhost:8001/metrics
# Should return Prometheus metrics
```

#### Check Logs

```bash
curl http://localhost:8001/logs
# Should return recent prediction logs
```

### 6. Test the Full Workflow

#### Make Multiple Predictions

```bash
# Test with different housing data
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "longitude": -118.25,
    "latitude": 34.05,
    "housing_median_age": 35.0,
    "total_rooms": 1500.0,
    "total_bedrooms": 200.0,
    "population": 500.0,
    "households": 150.0,
    "median_income": 7.5
  }'
```

#### Check Retraining Endpoints

```bash
# Check model performance
curl http://localhost:8001/model/performance

# Check for data drift
curl http://localhost:8001/model/drift

# Trigger manual retraining
curl -X POST http://localhost:8001/retrain \
  -H "Content-Type: application/json" \
  -d '{"trigger_type": "manual", "force": true}'
```

### 7. Monitor and Debug (if needed)

#### View Container Logs

```bash
# API logs
docker logs california-housing-api

# Or if using docker-compose
docker-compose logs -f api
```

#### Check File Permissions

```bash
# Ensure logs directory is writable
ls -la logs/
# Should show the container can write to this directory
```

### 8. Cleanup (when done)

```bash
# Stop everything
./scripts/deploy-local.sh stop

# Or with docker-compose
docker-compose down

# Remove containers
./scripts/deploy-local.sh remove
```

## 🎯 Quick Start Commands (Copy-Paste Ready)

```bash
# 1. Pull the image
docker pull YOUR_DOCKER_USERNAME/california-housing-mlops:latest

# 2. Start everything
./scripts/deploy-local.sh start

# 3. Test everything
./scripts/test-api.sh all

# 4. Open in browser
open http://localhost:8001/docs
open http://localhost:5002
open http://localhost:3000
```

## ⚠️ Important Notes

1. **Replace `YOUR_DOCKER_USERNAME`** with your actual Docker Hub username
2. **Ensure ports 8001, 5002, 9090, 3000** are available on your machine
3. **The first run might take a few minutes** as it downloads and starts all services
4. **Check the logs** if something doesn't work immediately

## 🔍 Troubleshooting Quick Tips

- **Port already in use**: Stop other services using those ports
- **Permission denied**: Make sure the scripts are executable (`chmod +x scripts/*.sh`)
- **Container won't start**: Check logs with `docker logs <container_name>`
- **API not responding**: Wait a few seconds for the container to fully start

## 📱 Monitoring the CI/CD Pipeline

1. **Go to GitHub**: `nrvivek75/group-52-california-housing-mlops`
2. **Click Actions tab**: Watch the pipeline progress
3. **Look for**: Green checkmarks ✅ instead of red X's ❌
4. **Wait for**: "Build and Push" job to complete successfully

## 🎉 Success Indicators

- ✅ All containers running (`docker ps` shows active containers)
- ✅ API responds to health check
- ✅ Predictions return valid results
- ✅ MLflow UI accessible
- ✅ Prometheus metrics visible
- ✅ Grafana dashboards working

## 🆘 Getting Help

If you encounter issues:

1. **Check container logs**: `docker logs <container_name>`
2. **Verify ports**: `netstat -an | grep LISTEN | grep -E "(8001|5002|9090|3000)"`
3. **Check file permissions**: Ensure scripts are executable
4. **Restart services**: Use `./scripts/deploy-local.sh restart`

---

**Once you complete these steps, you'll have a fully functional MLOps pipeline running locally! 🚀** 