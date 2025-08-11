#!/bin/bash
# Production Deployment Script for MLOps
# Handles production deployment with proper validation and rollback

set -e

# Configuration
DOCKER_IMAGE="california-housing-mlops"
DOCKER_TAG="latest"
CONTAINER_NAME="california-housing-mlops-prod"
NETWORK_NAME="mlops-network"
VOLUME_PREFIX="mlops-prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to create Docker network
create_network() {
    log_info "Creating Docker network..."
    
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        docker network create "$NETWORK_NAME"
        log_success "Network $NETWORK_NAME created"
    else
        log_info "Network $NETWORK_NAME already exists"
    fi
}

# Function to create Docker volumes
create_volumes() {
    log_info "Creating Docker volumes..."
    
    local volumes=("${VOLUME_PREFIX}-logs" "${VOLUME_PREFIX}-models" "${VOLUME_PREFIX}-mlruns" "${VOLUME_PREFIX}-data")
    
    for volume in "${volumes[@]}"; do
        if ! docker volume ls | grep -q "$volume"; then
            docker volume create "$volume"
            log_success "Volume $volume created"
        else
            log_info "Volume $volume already exists"
        fi
    done
}

# Function to stop existing container
stop_existing_container() {
    log_info "Checking for existing container..."
    
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        log_info "Stopping existing container $CONTAINER_NAME..."
        docker stop "$CONTAINER_NAME" || true
        docker rm "$CONTAINER_NAME" || true
        log_success "Existing container stopped and removed"
    else
        log_info "No existing container found"
    fi
}

# Function to pull latest image
pull_latest_image() {
    log_info "Pulling latest Docker image..."
    
    if docker pull "$DOCKER_IMAGE:$DOCKER_TAG"; then
        log_success "Latest image pulled successfully"
    else
        log_error "Failed to pull latest image"
        exit 1
    fi
}

# Function to deploy container
deploy_container() {
    log_info "Deploying new container..."
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        --restart unless-stopped \
        -p 8001:8001 \
        -p 5002:5002 \
        -p 9090:9090 \
        -p 3000:3000 \
        -v "${VOLUME_PREFIX}-logs:/app/logs" \
        -v "${VOLUME_PREFIX}-models:/app/models" \
        -v "${VOLUME_PREFIX}-mlruns:/app/mlruns" \
        -v "${VOLUME_PREFIX}-data:/app/data" \
        --memory="2g" \
        --cpus="2.0" \
        "$DOCKER_IMAGE:$DOCKER_TAG"
    
    if [ $? -eq 0 ]; then
        log_success "Container deployed successfully"
    else
        log_error "Failed to deploy container"
        exit 1
    fi
}

# Function to wait for services
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    local max_wait=300  # 5 minutes
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if curl -s "http://localhost:8001/health" > /dev/null 2>&1; then
            log_success "API service is ready"
            break
        fi
        
        echo "   Waiting for API service... (${wait_time}s/${max_wait}s)"
        sleep 10
        wait_time=$((wait_time + 10))
    done
    
    if [ $wait_time -ge $max_wait ]; then
        log_warning "API service not ready after ${max_wait}s, continuing..."
    fi
}

# Function to validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    local validation_passed=true
    
    # Check container status
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        log_error "Container is not running"
        validation_passed=false
    fi
    
    # Check API health
    if ! curl -s "http://localhost:8001/health" > /dev/null 2>&1; then
        log_error "API health check failed"
        validation_passed=false
    fi
    
    # Check MLflow
    if ! curl -s "http://localhost:5002" > /dev/null 2>&1; then
        log_warning "MLflow service not accessible"
    fi
    
    # Check Prometheus
    if ! curl -s "http://localhost:9090/-/healthy" > /dev/null 2>&1; then
        log_warning "Prometheus service not accessible"
    fi
    
    # Check Grafana
    if ! curl -s "http://localhost:3000/api/health" > /dev/null 2>&1; then
        log_warning "Grafana service not accessible"
    fi
    
    if [ "$validation_passed" = true ]; then
        log_success "Deployment validation passed"
        return 0
    else
        log_error "Deployment validation failed"
        return 1
    fi
}

# Function to rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."
    
    # Stop current container
    docker stop "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
    
    # Start previous version if available
    if docker images | grep -q "$DOCKER_IMAGE"; then
        log_info "Attempting to start previous version..."
        deploy_container
        wait_for_services
    fi
    
    log_error "Rollback completed"
}

# Function to show deployment status
show_status() {
    log_info "Deployment status:"
    
    echo "Container: $CONTAINER_NAME"
    echo "Status: $(docker ps --filter name=$CONTAINER_NAME --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
    echo "Image: $DOCKER_IMAGE:$DOCKER_TAG"
    echo "Network: $NETWORK_NAME"
    echo ""
    echo "Service endpoints:"
    echo "  API: http://localhost:8001"
    echo "  MLflow: http://localhost:5002"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000"
    echo ""
    echo "Volumes:"
    docker volume ls | grep "$VOLUME_PREFIX" || echo "No volumes found"
}

# Main deployment function
main() {
    log_info "Starting production deployment..."
    
    # Check prerequisites
    check_prerequisites
    
    # Create infrastructure
    create_network
    create_volumes
    
    # Stop existing container
    stop_existing_container
    
    # Pull latest image
    pull_latest_image
    
    # Deploy new container
    deploy_container
    
    # Wait for services
    wait_for_services
    
    # Validate deployment
    if validate_deployment; then
        log_success "🎉 Production deployment completed successfully!"
        show_status
    else
        log_error "❌ Deployment validation failed"
        rollback_deployment
        exit 1
    fi
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_status
        ;;
    "stop")
        log_info "Stopping production container..."
        docker stop "$CONTAINER_NAME" || true
        docker rm "$CONTAINER_NAME" || true
        log_success "Production container stopped"
        ;;
    "logs")
        log_info "Showing container logs..."
        docker logs -f "$CONTAINER_NAME"
        ;;
    "restart")
        log_info "Restarting production container..."
        docker restart "$CONTAINER_NAME"
        log_success "Production container restarted"
        ;;
    *)
        echo "Usage: $0 {deploy|status|stop|logs|restart}"
        echo "  deploy   - Deploy new version (default)"
        echo "  status   - Show deployment status"
        echo "  stop     - Stop production container"
        echo "  logs     - Show container logs"
        echo "  restart  - Restart production container"
        exit 1
        ;;
esac 