# 🚀 Deployment Guide - California Housing MLOps

This guide explains how to deploy and test the California Housing MLOps project after pushing to GitHub.

## 📋 Prerequisites

- Docker installed and running
- Git configured
- Access to Docker Hub (optional, for pulling pre-built images)

## 🔄 Workflow Overview

1. **Push to GitHub** → Triggers CI/CD pipeline
2. **CI/CD Builds** → Creates Docker image and pushes to Docker Hub
3. **Local Deployment** → Pull image and run container locally
4. **Testing** → Verify all endpoints and functionality

## 🚀 Step-by-Step Deployment

### Step 1: Push to GitHub

```bash
# Add all changes
git add .

# Commit changes
git commit -m "Ready for CI/CD deployment"

# Push to GitHub (this triggers the CI/CD pipeline)
git push origin main
```

### Step 2: Monitor CI/CD Pipeline

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Monitor the CI/CD pipeline progress:
   - ✅ Lint and Test
   - ✅ Build and Push Docker Image
   - ✅ Comment on PR (if applicable)

### Step 3: Local Deployment

Once the CI/CD pipeline completes successfully, deploy locally:

#### Option A: Using the Deployment Script (Recommended)

```bash
# Make script executable (if not already done)
chmod +x scripts/deploy-local.sh

# Deploy using Docker Hub image (replace 'yourusername' with your Docker Hub username)
DOCKER_USERNAME=yourusername ./scripts/deploy-local.sh start

# Or deploy without Docker Hub (will use local image if available)
./scripts/deploy-local.sh start
```

#### Option B: Manual Docker Commands

```bash
# Pull the latest image from Docker Hub
docker pull yourusername/california-housing-mlops:latest

# Run the container
docker run -d \
  --name california-housing-api \
  --restart unless-stopped \
  -p 8001:8001 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/mlruns:/app/mlruns \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  yourusername/california-housing-mlops:latest
```

#### Option C: Using Docker Compose

```bash
# Start all services (API, MLflow, Prometheus, Grafana)
docker-compose up -d

# View logs
docker-compose logs -f california-housing-api
```

### Step 4: Verify Deployment

```bash
# Check container status
./scripts/deploy-local.sh status

# Check health endpoint
curl http://localhost:8001/health

# View container logs
./scripts/deploy-local.sh logs
```

## 🌐 Access Points

After successful deployment, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8001 | Main FastAPI application |
| **Health** | http://localhost:8001/health | Health check endpoint |
| **Metrics** | http://localhost:8001/metrics | API metrics and statistics |
| **Logs** | http://localhost:8001/logs | Recent prediction logs |
| **API Docs** | http://localhost:8001/docs | Interactive API documentation |
| **MLflow UI** | http://localhost:5002 | Experiment tracking (if using docker-compose) |
| **Prometheus** | http://localhost:9090 | Metrics collection (if using docker-compose) |
| **Grafana** | http://localhost:3000 | Dashboards (if using docker-compose) |

## 🧪 Testing the API

### Health Check
```bash
curl http://localhost:8001/health
```

### Make a Prediction
```bash
curl -X POST "http://localhost:8001/predict" \
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

### Get Metrics
```bash
curl http://localhost:8001/metrics
```

### Get Logs
```bash
curl http://localhost:8001/logs?limit=5
```

## 🛠️ Management Commands

```bash
# Start container
./scripts/deploy-local.sh start

# Stop container
./scripts/deploy-local.sh stop

# Restart container
./scripts/deploy-local.sh restart

# Remove container
./scripts/deploy-local.sh remove

# Check status
./scripts/deploy-local.sh status

# View logs
./scripts/deploy-local.sh logs

# Show help
./scripts/deploy-local.sh help
```

## 🔍 Troubleshooting

### Container Won't Start
```bash
# Check Docker logs
docker logs california-housing-api

# Check if port is already in use
lsof -i :8001

# Verify Docker is running
docker info
```

### Image Pull Fails
```bash
# Check if you're logged into Docker Hub
docker login

# Verify image exists
docker search yourusername/california-housing-mlops

# Build locally if needed
docker build -t california-housing-mlops:latest .
```

### Health Check Fails
```bash
# Check container status
docker ps -a

# Check container logs
docker logs california-housing-api

# Verify required files exist
ls -la logs/ models/ mlruns/
```

### Port Conflicts
```bash
# Check what's using port 8001
lsof -i :8001

# Kill process if needed
kill -9 <PID>

# Or use a different port
docker run -p 8002:8001 ... # Maps host port 8002 to container port 8001
```

## 📊 Monitoring

### View Real-time Logs
```bash
# Follow API logs
tail -f logs/api.log

# Follow container logs
docker logs -f california-housing-api
```

### Check Resource Usage
```bash
# Container resource usage
docker stats california-housing-api

# Disk usage
du -sh logs/ mlruns/ models/
```

### Performance Testing
```bash
# Simple load test
for i in {1..10}; do
  curl -X POST "http://localhost:8001/predict" \
       -H "Content-Type: application/json" \
       -d '{"longitude": -122.23, "latitude": 37.88, "housing_median_age": 41.0, "total_rooms": 880.0, "total_bedrooms": 129.0, "population": 322.0, "households": 126.0, "median_income": 8.3252}' &
done
wait
```

## 🔄 Updating the Deployment

When you push new changes to GitHub:

1. **Wait for CI/CD** to complete
2. **Pull the new image**:
   ```bash
   docker pull yourusername/california-housing-mlops:latest
   ```
3. **Restart the container**:
   ```bash
   ./scripts/deploy-local.sh restart
   ```

## 📝 Environment Variables

You can customize the deployment by setting environment variables:

```bash
# Use specific Docker Hub username
export DOCKER_USERNAME=yourusername

# Use specific port
export PORT=8002

# Deploy with custom settings
./scripts/deploy-local.sh start
```

## 🎯 Next Steps

After successful deployment:

1. **Test all API endpoints** to ensure functionality
2. **Monitor logs** for any errors or issues
3. **Check metrics** to understand API performance
4. **Explore MLflow UI** to view experiment tracking
5. **Customize configurations** as needed for your environment

---

**Happy Deploying! 🚀**

For issues or questions, check the troubleshooting section or review the main README.md file. 