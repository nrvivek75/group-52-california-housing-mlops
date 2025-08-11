# 🚀 All-in-One MLOps Docker Deployment Guide

## 🎯 **What This Achieves**

This guide shows you how to deploy **ALL 4 MLOps services** using just **ONE Docker image**:

- ✅ **FastAPI API** (Port 8001)
- ✅ **MLflow UI** (Port 5002) 
- ✅ **Prometheus** (Port 9090)
- ✅ **Grafana** (Port 3000)

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    Single Docker Container                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────┐ │
│  │   FastAPI   │ │   MLflow    │ │ Prometheus  │ │Grafana│ │
│  │   (8001)    │ │   (5002)    │ │   (9090)    │ │(3000) │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────┘ │
│                                                             │
│  Supervisor manages all 4 services                         │
│  All services share the same filesystem                     │
│  Single health check endpoint                               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 **Quick Start (3 Steps)**

### **Step 1: Build the All-in-One Image**
```bash
# Option A: Use the script (recommended)
./scripts/start-all-in-one.sh build

# Option B: Use docker-compose
docker-compose -f docker-compose.all-in-one.yml build

# Option C: Manual Docker build
docker build -f Dockerfile.all-in-one -t mlops-all-in-one:latest .
```

### **Step 2: Start All Services**
```bash
# Option A: Use the script (recommended)
./scripts/start-all-in-one.sh start

# Option B: Use docker-compose
docker-compose -f docker-compose.all-in-one.yml up -d

# Option C: Manual Docker run
docker run -d \
  --name mlops-all-in-one \
  -p 8001:8001 -p 5002:5002 -p 9090:9090 -p 3000:3000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/mlruns:/app/mlruns \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  mlops-all-in-one:latest
```

### **Step 3: Access Your Services**
```
🌐 FastAPI API:     http://localhost:8001
📊 MLflow UI:       http://localhost:5002
📈 Prometheus:      http://localhost:9090
📊 Grafana:         http://localhost:3000 (admin/admin)
```

## 📋 **Prerequisites**

- ✅ Docker installed and running
- ✅ At least 4GB RAM available
- ✅ Ports 8001, 5002, 9090, 3000 available

## 🔧 **Detailed Setup**

### **1. Using the Script (Recommended)**

The `scripts/start-all-in-one.sh` script handles everything automatically:

```bash
# Start everything
./scripts/start-all-in-one.sh start

# Check status
./scripts/start-all-in-one.sh status

# View logs
./scripts/start-all-in-one.sh logs

# Stop services
./scripts/start-all-in-one.sh stop

# Remove container
./scripts/start-all-in-one.sh remove

# Get help
./scripts/start-all-in-one.sh help
```

### **2. Using Docker Compose**

```bash
# Build and start
docker-compose -f docker-compose.all-in-one.yml up -d

# View logs
docker-compose -f docker-compose.all-in-one.yml logs -f

# Stop
docker-compose -f docker-compose.all-in-one.yml down
```

### **3. Manual Docker Commands**

```bash
# Build image
docker build -f Dockerfile.all-in-one -t mlops-all-in-one:latest .

# Run container
docker run -d \
  --name mlops-all-in-one \
  -p 8001:8001 -p 5002:5002 -p 9090:9090 -p 3000:3000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/mlruns:/app/mlruns \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  mlops-all-in-one:latest

# Check status
docker ps

# View logs
docker logs -f mlops-all-in-one

# Stop
docker stop mlops-all-in-one

# Remove
docker rm mlops-all-in-one
```

## 🔍 **What's Inside the Image**

### **Base Image**
- Python 3.11 slim
- System tools (curl, wget, supervisor, sqlite3)

### **Services**
1. **FastAPI Application** (`src/api.py`)
2. **MLflow UI** (Python package)
3. **Prometheus** (Downloaded binary)
4. **Grafana** (Downloaded binary)

### **Process Management**
- **Supervisor** manages all 4 services
- Automatic restart on failure
- Centralized logging
- Health monitoring

### **Configuration**
- Prometheus config for metrics scraping
- Grafana provisioning for dashboards
- MLflow backend configuration
- Volume mounts for persistence

## 📊 **Service Details**

### **FastAPI API (Port 8001)**
- Housing price prediction endpoint
- Health checks
- Metrics endpoint for Prometheus
- Logging and monitoring
- Model retraining triggers

### **MLflow UI (Port 5002)**
- Experiment tracking
- Model registry
- Artifact storage
- Model versioning

### **Prometheus (Port 9090)**
- Metrics collection
- API performance monitoring
- MLflow metrics
- Self-monitoring

### **Grafana (Port 3000)**
- Pre-configured dashboards
- Prometheus data source
- Real-time monitoring
- Performance visualization

## 🔄 **Workflow Integration**

### **CI/CD Pipeline**
1. Build the all-in-one image
2. Push to Docker Hub
3. Deploy anywhere with one command

### **Local Development**
1. Build once
2. Start with one command
3. All services available immediately

### **Production Deployment**
1. Single image deployment
2. Unified health monitoring
3. Simplified orchestration

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Check what's using the ports
lsof -i :8001
lsof -i :5002
lsof -i :9090
lsof -i :3000

# Stop conflicting services
docker stop $(docker ps -q)
```

#### **Container Won't Start**
```bash
# Check logs
docker logs mlops-all-in-one

# Check resource usage
docker stats mlops-all-in-one

# Restart container
docker restart mlops-all-in-one
```

#### **Services Not Responding**
```bash
# Check container status
docker ps -a

# Check service health
curl http://localhost:8001/health
curl http://localhost:5002
curl http://localhost:9090
curl http://localhost:3000
```

### **Debug Commands**
```bash
# Enter container
docker exec -it mlops-all-in-one bash

# Check supervisor status
supervisorctl status

# Check individual service logs
supervisorctl tail api
supervisorctl tail mlflow
supervisorctl tail prometheus
supervisorctl tail grafana

# Restart specific service
supervisorctl restart api
```

## 📈 **Performance Considerations**

### **Resource Requirements**
- **Minimum**: 2GB RAM, 2 CPU cores
- **Recommended**: 4GB RAM, 4 CPU cores
- **Storage**: 5GB+ for models and data

### **Optimization Tips**
- Use volume mounts for persistent data
- Monitor resource usage with `docker stats`
- Adjust supervisor restart policies if needed
- Consider resource limits for production

## 🔐 **Security Notes**

- Grafana admin password: `admin`
- All services bind to `0.0.0.0` (accessible from any IP)
- Consider firewall rules for production
- Volume mounts preserve data between restarts

## 🎉 **Benefits of This Approach**

1. **🚀 Single Command Deployment**: One image, all services
2. **🔧 Simplified Management**: Single container to monitor
3. **📦 Consistent Environment**: All services use same base image
4. **🔄 Easy Scaling**: Copy image to any host
5. **📊 Unified Monitoring**: Single health check endpoint
6. **💾 Persistent Data**: Volume mounts preserve your work
7. **🛠️ Development Friendly**: Quick local setup and testing

## 📚 **Next Steps**

1. **Build and test** the all-in-one image locally
2. **Push to Docker Hub** for distribution
3. **Deploy on any host** with one command
4. **Customize dashboards** and monitoring
5. **Scale horizontally** by running multiple instances

---

**🎯 Goal Achieved**: You now have a **single Docker image** that contains **all 4 MLOps services** and can be deployed with **one command**! 