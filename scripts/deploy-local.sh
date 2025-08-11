#!/bin/bash
# Local Deployment Script for California Housing MLOps
# This script pulls the Docker image from Docker Hub and runs it locally
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="california-housing-mlops"
CONTAINER_NAME="california-housing-api"
PORT="8001"
DOCKER_USERNAME=""

# Helper functions
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

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Docker is available"
}

get_docker_username() {
    if [ -z "$DOCKER_USERNAME" ]; then
        echo -n "Enter your Docker Hub username: "
        read -r DOCKER_USERNAME
        if [ -z "$DOCKER_USERNAME" ]; then
            log_error "Docker Hub username is required"
            exit 1
        fi
    fi
}

cleanup_container() {
    if docker ps -a --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        log_info "Removing existing container..."
        docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    fi
}

pull_image() {
    log_info "Pulling latest Docker image..."
    docker pull "$DOCKER_USERNAME/$IMAGE_NAME:latest"
    
    if [ $? -eq 0 ]; then
        log_success "Image pulled successfully!"
    else
        log_error "Failed to pull image"
        exit 1
    fi
}

create_directories() {
    log_info "Creating necessary directories..."
    mkdir -p logs mlruns models data
    log_success "Directories created"
}

run_container() {
    log_info "Starting container..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$PORT:$PORT" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/mlruns:/app/mlruns" \
        -v "$(pwd)/models:/app/models" \
        -v "$(pwd)/data:/app/data" \
        "$DOCKER_USERNAME/$IMAGE_NAME:latest"
    
    if [ $? -eq 0 ]; then
        log_success "Container started successfully!"
    else
        log_error "Failed to start container"
        exit 1
    fi
}

wait_for_container() {
    log_info "Waiting for container to be ready..."
    local count=0
    while [ $count -lt 30 ]; do
        if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
            log_success "Container is ready!"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    log_error "Container failed to start within 30 seconds"
    exit 1
}

show_status() {
    log_success "Local MLOps Stack is Running!"
    echo
    echo "Container Status:"
    docker ps --filter "name=$CONTAINER_NAME"
    echo
    echo "Access Points:"
    echo "  API: http://localhost:$PORT"
    echo "  Health: http://localhost:$PORT/health"
    echo "  Metrics: http://localhost:$PORT/metrics"
    echo "  Logs: http://localhost:$PORT/logs"
    echo
    echo "Commands:"
    echo "  View logs:          docker logs -f $CONTAINER_NAME"
    echo "  Stop:               docker stop $CONTAINER_NAME"
    echo "  Remove:             docker rm $CONTAINER_NAME"
    echo "  Restart:            docker restart $CONTAINER_NAME"
}

main() {
    local command=${1:-start}
    
    case $command in
        start)
            check_docker
            get_docker_username
            cleanup_container
            pull_image
            create_directories
            run_container
            wait_for_container
            show_status
            ;;
        stop)
            log_info "Stopping container..."
            docker stop "$CONTAINER_NAME" 2>/dev/null || true
            log_success "Container stopped"
            ;;
        restart)
            log_info "Restarting container..."
            docker restart "$CONTAINER_NAME" 2>/dev/null || true
            log_success "Container restarted"
            ;;
        remove)
            log_info "Removing container..."
            docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
            log_success "Container removed"
            ;;
        logs)
            docker logs -f "$CONTAINER_NAME"
            ;;
        status)
            if docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
                log_success "Container is running"
                docker ps --filter "name=$CONTAINER_NAME"
            else
                log_warning "Container is not running"
            fi
            ;;
        help|*)
            echo "Usage: $0 [start|stop|restart|remove|logs|status|help]"
            echo
            echo "Commands:"
            echo "  start   - Pull image and start container (default)"
            echo "  stop    - Stop the container"
            echo "  restart - Restart the container"
            echo "  remove  - Remove the container"
            echo "  logs    - View container logs"
            echo "  status  - Check container status"
            echo "  help    - Show this help message"
            ;;
    esac
}

main "$@" 