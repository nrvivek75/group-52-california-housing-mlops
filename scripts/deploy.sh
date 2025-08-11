#!/bin/bash

# Deployment script for California Housing MLOps API
# Usage: ./scripts/deploy.sh [local|remote] [dockerhub-username]

set -e

DEPLOYMENT_TYPE=${1:-local}
DOCKER_USERNAME=${2:-"your-dockerhub-username"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting deployment for California Housing MLOps API${NC}"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to build Docker image
build_image() {
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    docker build -t california-housing-mlops:latest .
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
}

# Function to deploy locally
deploy_local() {
    echo -e "${YELLOW}🏠 Deploying locally...${NC}"
    
    # Stop existing container if running
    if docker ps -q -f name=california-housing-api | grep -q .; then
        echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
        docker stop california-housing-api
        docker rm california-housing-api
    fi
    
    # Create logs and mlruns directories if they don't exist
    mkdir -p logs mlruns
    
    # Run container
    docker run -d \
        --name california-housing-api \
        --restart unless-stopped \
        -p 8000:8000 \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/mlruns:/app/mlruns" \
        california-housing-mlops:latest
    
    echo -e "${GREEN}✅ Local deployment completed!${NC}"
    echo -e "${GREEN}🌐 API is running at: http://localhost:8000${NC}"
    echo -e "${GREEN}📊 Health check: http://localhost:8000/health${NC}"
    echo -e "${GREEN}📈 Metrics: http://localhost:8000/metrics${NC}"
}

# Function to deploy remotely
deploy_remote() {
    echo -e "${YELLOW}☁️  Deploying remotely...${NC}"
    
    # Pull latest image from Docker Hub
    echo -e "${YELLOW}📥 Pulling latest image from Docker Hub...${NC}"
    docker pull ${DOCKER_USERNAME}/california-housing-mlops:latest
    
    # Stop existing container if running
    if docker ps -q -f name=california-housing-api | grep -q .; then
        echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
        docker stop california-housing-api
        docker rm california-housing-api
    fi
    
    # Run container
    docker run -d \
        --name california-housing-api \
        --restart unless-stopped \
        -p 8000:8000 \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/mlruns:/app/mlruns" \
        ${DOCKER_USERNAME}/california-housing-mlops:latest
    
    echo -e "${GREEN}✅ Remote deployment completed!${NC}"
    echo -e "${GREEN}🌐 API is running at: http://localhost:8000${NC}"
}

# Function to check deployment status
check_status() {
    echo -e "${YELLOW}🔍 Checking deployment status...${NC}"
    
    if docker ps -q -f name=california-housing-api | grep -q .; then
        echo -e "${GREEN}✅ Container is running${NC}"
        docker ps -f name=california-housing-api
        
        # Health check
        echo -e "${YELLOW}🏥 Performing health check...${NC}"
        sleep 5
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Health check passed${NC}"
        else
            echo -e "${RED}❌ Health check failed${NC}"
        fi
    else
        echo -e "${RED}❌ Container is not running${NC}"
    fi
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}📋 Container logs:${NC}"
    docker logs california-housing-api --tail=20
}

# Function to stop deployment
stop_deployment() {
    echo -e "${YELLOW}🛑 Stopping deployment...${NC}"
    
    if docker ps -q -f name=california-housing-api | grep -q .; then
        docker stop california-housing-api
        docker rm california-housing-api
        echo -e "${GREEN}✅ Deployment stopped${NC}"
    else
        echo -e "${YELLOW}ℹ️  No running deployment found${NC}"
    fi
}

# Main deployment logic
case $DEPLOYMENT_TYPE in
    "local")
        check_docker
        build_image
        deploy_local
        check_status
        ;;
    "remote")
        if [ -z "$DOCKER_USERNAME" ] || [ "$DOCKER_USERNAME" = "your-dockerhub-username" ]; then
            echo -e "${RED}❌ Please provide your Docker Hub username${NC}"
            echo "Usage: ./scripts/deploy.sh remote your-dockerhub-username"
            exit 1
        fi
        check_docker
        deploy_remote
        check_status
        ;;
    "status")
        check_status
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop_deployment
        ;;
    *)
        echo -e "${RED}❌ Invalid deployment type. Use: local, remote, status, logs, or stop${NC}"
        echo "Usage: ./scripts/deploy.sh [local|remote|status|logs|stop] [dockerhub-username]"
        exit 1
        ;;
esac

echo -e "${GREEN}🎉 Deployment script completed!${NC}" 