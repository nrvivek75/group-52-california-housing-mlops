#!/bin/bash

# All-in-One MLOps Docker Image Script
# This script builds and runs a single Docker image containing all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

cleanup_container() {
    if docker ps -a --format "table {{.Names}}" | grep -q "mlops-all-in-one"; then
        log_info "Removing existing container..."
        docker rm -f mlops-all-in-one 2>/dev/null || true
    fi
}

build_image() {
    log_info "Building all-in-one MLOps Docker image..."
    docker build -f Dockerfile.all-in-one -t mlops-all-in-one:latest .
    
    if [ $? -eq 0 ]; then
        log_success "Image built successfully!"
    else
        log_error "Failed to build image"
        exit 1
    fi
}

run_container() {
    log_info "Starting all-in-one MLOps container..."
    docker run -d \
        --name mlops-all-in-one \
        -p 8001:8001 \
        -p 5002:5002 \
        -p 9090:9090 \
        -p 3000:3000 \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/mlruns:/app/mlruns" \
        -v "$(pwd)/models:/app/models" \
        -v "$(pwd)/data:/app/data" \
        mlops-all-in-one:latest
    
    if [ $? -eq 0 ]; then
        log_success "Container started successfully!"
    else
        log_error "Failed to start container"
        exit 1
    fi
}

wait_for_services() {
    log_info "Waiting for services to start up..."
    
    # Wait for API
    log_info "Waiting for API (port 8001)..."
    for i in {1..30}; do
        if curl -s http://localhost:8001/health >/dev/null 2>&1; then
            log_success "API is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "API failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
    
    # Wait for MLflow
    log_info "Waiting for MLflow (port 5002)..."
    for i in {1..30}; do
        if curl -s http://localhost:5002 >/dev/null 2>&1; then
            log_success "MLflow is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            log_warning "MLflow may not be ready yet"
        fi
        sleep 1
    done
    
    # Wait for Prometheus
    log_info "Waiting for Prometheus (port 9090)..."
    for i in {1..30}; do
        if curl -s http://localhost:9090 >/dev/null 2>&1; then
            log_success "Prometheus is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            log_warning "Prometheus may not be ready yet"
        fi
        sleep 1
    done
    
    # Wait for Grafana
    log_info "Waiting for Grafana (port 3000)..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            log_success "Grafana is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            log_warning "Grafana may not be ready yet"
        fi
        sleep 1
    done
}

show_status() {
    log_success "🎉 All-in-One MLOps Stack is Running!"
    echo
    echo "📊 Services Status:"
    echo "  ✅ FastAPI API:     http://localhost:8001"
    echo "  ✅ MLflow UI:       http://localhost:5002"
    echo "  ✅ Prometheus:      http://localhost:9090"
    echo "  ✅ Grafana:         http://localhost:3000 (admin/admin)"
    echo
    echo "🔗 Quick Links:"
    echo "  📈 API Docs:        http://localhost:8001/docs"
    echo "  🧪 MLflow:          http://localhost:5002"
    echo "  📊 Prometheus:      http://localhost:9090"
    echo "  📈 Grafana:         http://localhost:3000"
    echo
    echo "📝 Commands:"
    echo "  View logs:          docker logs -f mlops-all-in-one"
    echo "  Stop:               docker stop mlops-all-in-one"
    echo "  Remove:             docker rm mlops-all-in-one"
    echo "  Restart:            docker restart mlops-all-in-one"
}

main() {
    local command=${1:-start}
    
    case $command in
        start)
            check_docker
            cleanup_container
            build_image
            run_container
            wait_for_services
            show_status
            ;;
        stop)
            log_info "Stopping container..."
            docker stop mlops-all-in-one 2>/dev/null || true
            log_success "Container stopped"
            ;;
        restart)
            log_info "Restarting container..."
            docker restart mlops-all-in-one 2>/dev/null || true
            log_success "Container restarted"
            ;;
        remove)
            log_info "Removing container..."
            docker rm -f mlops-all-in-one 2>/dev/null || true
            log_success "Container removed"
            ;;
        logs)
            docker logs -f mlops-all-in-one
            ;;
        status)
            if docker ps --format "table {{.Names}}" | grep -q "mlops-all-in-one"; then
                log_success "Container is running"
                docker ps --filter "name=mlops-all-in-one"
            else
                log_warning "Container is not running"
            fi
            ;;
        build)
            check_docker
            build_image
            ;;
        help|*)
            echo "Usage: $0 [start|stop|restart|remove|logs|status|build|help]"
            echo
            echo "Commands:"
            echo "  start   - Build and start the all-in-one container (default)"
            echo "  stop    - Stop the container"
            echo "  restart - Restart the container"
            echo "  remove  - Remove the container"
            echo "  logs    - View container logs"
            echo "  status  - Check container status"
            echo "  build   - Build the image only"
            echo "  help    - Show this help message"
            ;;
    esac
}

main "$@" 