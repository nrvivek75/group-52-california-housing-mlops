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
DOCKER_IMAGE="california-housing-mlops"
CONTAINER_NAME="california-housing-api"
PORT="8001"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if container exists
container_exists() {
    docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# Function to check if container is running
container_running() {
    docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# Function to stop and remove existing container
cleanup_container() {
    if container_exists; then
        print_status "Stopping existing container..."
        docker stop ${CONTAINER_NAME} > /dev/null 2>&1 || true
        docker rm ${CONTAINER_NAME} > /dev/null 2>&1 || true
        print_success "Existing container cleaned up"
    fi
}

# Function to pull latest image
pull_image() {
    print_status "Pulling latest Docker image..."
    
    # Check if DOCKER_USERNAME is set
    if [ -z "$DOCKER_USERNAME" ]; then
        print_warning "DOCKER_USERNAME not set. Using default image name."
        if ! docker pull ${DOCKER_IMAGE}:latest; then
            print_error "Failed to pull image. Please build locally first:"
            print_status "docker build -t ${DOCKER_IMAGE}:latest ."
            exit 1
        fi
    else
        if ! docker pull ${DOCKER_USERNAME}/${DOCKER_IMAGE}:latest; then
            print_error "Failed to pull image from Docker Hub."
            print_status "Make sure the image exists and you have access to it."
            exit 1
        fi
        DOCKER_IMAGE="${DOCKER_USERNAME}/${DOCKER_IMAGE}"
    fi
    
    print_success "Docker image pulled successfully"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p logs mlruns models data/raw data/processed
    print_success "Directories created"
}

# Function to run container
run_container() {
    print_status "Starting container..."
    
    if [ -z "$DOCKER_USERNAME" ]; then
        # Use local image
        docker run -d \
            --name ${CONTAINER_NAME} \
            --restart unless-stopped \
            -p ${PORT}:8001 \
            -v $(pwd)/logs:/app/logs \
            -v $(pwd)/mlruns:/app/mlruns \
            -v $(pwd)/models:/app/models \
            -v $(pwd)/data:/app/data \
            ${DOCKER_IMAGE}:latest
    else
        # Use Docker Hub image
        docker run -d \
            --name ${CONTAINER_NAME} \
            --restart unless-stopped \
            -p ${PORT}:8001 \
            -v $(pwd)/logs:/app/logs \
            -v $(pwd)/mlruns:/app/mlruns \
            -v $(pwd)/models:/app/models \
            -v $(pwd)/data:/app/data \
            ${DOCKER_IMAGE}:latest
    fi
    
    print_success "Container started successfully"
}

# Function to wait for container to be ready
wait_for_container() {
    print_status "Waiting for container to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:${PORT}/health > /dev/null 2>&1; then
            print_success "Container is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - Container not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Container failed to become ready within expected time"
    return 1
}

# Function to show container status
show_status() {
    print_status "Container Status:"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    print_status "Access URLs:"
    echo -e "  🌐 API: ${BLUE}http://localhost:${PORT}${NC}"
    echo -e "  📊 Health: ${BLUE}http://localhost:${PORT}/health${NC}"
    echo -e "  📈 Metrics: ${BLUE}http://localhost:${PORT}/metrics${NC}"
    echo -e "  📝 Logs: ${BLUE}http://localhost:${PORT}/logs${NC}"
    echo -e "  🔮 Predict: ${BLUE}http://localhost:${PORT}/docs${NC}"
}

# Function to show logs
show_logs() {
    print_status "Container logs:"
    docker logs ${CONTAINER_NAME} --tail 20 -f
}

# Function to stop container
stop_container() {
    if container_running; then
        print_status "Stopping container..."
        docker stop ${CONTAINER_NAME}
        print_success "Container stopped"
    else
        print_warning "Container is not running"
    fi
}

# Function to remove container
remove_container() {
    if container_exists; then
        print_status "Removing container..."
        docker rm ${CONTAINER_NAME}
        print_success "Container removed"
    else
        print_warning "Container does not exist"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the container (default)"
    echo "  stop      Stop the container"
    echo "  restart   Restart the container"
    echo "  remove    Remove the container"
    echo "  status    Show container status"
    echo "  logs      Show container logs"
    echo "  help      Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DOCKER_USERNAME    Docker Hub username (optional)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start container"
    echo "  DOCKER_USERNAME=yourname $0 start  # Use Docker Hub image"
    echo "  $0 stop               # Stop container"
    echo "  $0 logs               # Show logs"
}

# Main script logic
main() {
    local command=${1:-start}
    
    case $command in
        start)
            check_docker
            cleanup_container
            pull_image
            create_directories
            run_container
            wait_for_container
            show_status
            ;;
        stop)
            stop_container
            ;;
        restart)
            stop_container
            sleep 2
            check_docker
            cleanup_container
            pull_image
            create_directories
            run_container
            wait_for_container
            show_status
            ;;
        remove)
            stop_container
            remove_container
            ;;
        status)
            if container_exists; then
                show_status
            else
                print_warning "Container does not exist"
            fi
            ;;
        logs)
            if container_exists; then
                show_logs
            else
                print_warning "Container does not exist"
            fi
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 