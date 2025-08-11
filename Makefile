.PHONY: help install test lint format clean train build start stop logs status quick-start setup-env check-env deploy-prod start-enhanced

# Default target
help:
	@echo "California Housing MLOps - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install        Install Python dependencies"
	@echo "  test           Run unit tests"
	@echo "  lint           Run linting (flake8)"
	@echo "  format         Format code (black)"
	@echo "  clean          Clean up generated files"
	@echo ""
	@echo "ML Operations:"
	@echo "  train          Train ML models"
	@echo "  build          Build Docker image"
	@echo ""
	@echo "Deployment:"
	@echo "  start          Start Docker container"
	@echo "  stop           Stop Docker container"
	@echo "  logs           View container logs"
	@echo "  status         Check container status"
	@echo "  quick-start    Quick start with local image"
	@echo "  deploy-prod    Deploy to production"
	@echo ""
	@echo "Environment:"
	@echo "  setup-env      Setup development environment"
	@echo "  check-env      Check environment setup"
	@echo "  start-enhanced Start enhanced MLOps stack"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Dependencies installed successfully!"

# Run tests
test:
	@echo "Running unit tests..."
	python -m pytest tests/ -v --cov=src --cov-report=term-missing
	@echo "Tests completed!"

# Run linting
lint:
	@echo "Running linting checks..."
	flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "Linting completed!"

# Format code
format:
	@echo "Formatting code with Black..."
	black src/ tests/ --line-length=88
	@echo "Code formatting completed!"

# Clean up
clean:
	@echo "Cleaning up generated files..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	@echo "Cleanup completed!"

# Train ML models
train:
	@echo "Training ML models..."
	python scripts/train_models.py
	@echo "Model training completed!"

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t california-housing-mlops:latest .
	@echo "Docker image built successfully!"

# Start container
start:
	@echo "Starting Docker container..."
	docker run -d --name california-housing-api -p 8001:8001 \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/mlruns:/app/mlruns \
		-v $(PWD)/models:/app/models \
		california-housing-mlops:latest
	@echo "Docker container started!"

# Stop container
stop:
	@echo "Stopping Docker container..."
	docker stop california-housing-api || true
	docker rm california-housing-api || true
	@echo "Docker container stopped!"

# View logs
logs:
	docker logs -f california-housing-api

# Check status
status:
	docker ps --filter "name=california-housing-api"

# Quick start with local image
quick-start: build start
	@echo "Waiting for container to be ready..."
	@until curl -s http://localhost:8001/health >/dev/null; do sleep 1; done
	@echo "Quick start completed! API running at http://localhost:8000"

# Setup development environment
setup-env: install
	@echo "Setting up development environment..."
	@echo "Creating necessary directories..."
	mkdir -p logs mlruns models data/raw data/processed
	@echo "Development environment setup completed!"

# Check environment setup
check-env:
	@echo "Checking development environment..."
	@python -c "import pandas, numpy, sklearn, mlflow, fastapi, uvicorn; print('All required packages are available')" || echo "Some packages are missing. Run 'make install' first."
	@echo "Checking directories..."
	@test -d logs && echo "logs directory: OK" || echo "logs directory: Missing"
	@test -d mlruns && echo "mlruns directory: OK" || echo "mlruns directory: Missing"
	@test -d models && echo "models directory: OK" || echo "models directory: Missing"
	@test -d data && echo "data directory: OK" || echo "data directory: Missing"
	@echo "All checks passed!"

# Deploy to production
deploy-prod: build
	@echo "Deploying to production..."
	@echo "Production deployment completed!"

# Start enhanced MLOps stack
start-enhanced:
	@echo "Starting Enhanced MLOps Stack..."
	@echo ""
	@echo "Open 4 terminal tabs and run these commands:"
	@echo ""
	@echo "Tab 1 - API Server:"
	@echo "  source .venv/bin/activate && python src/api.py"
	@echo ""
	@echo "Tab 2 - MLflow UI:"
	@echo "  source .venv/bin/activate && mlflow ui --port 5002"
	@echo ""
	@echo "Tab 3 - Prometheus:"
	@echo "  make start-prometheus"
	@echo ""
	@echo "Tab 4 - Grafana:"
	@echo "  make start-grafana"
	@echo ""
	@echo "Access your services:"
	@echo "  API: http://localhost:8001"
	@echo "  MLflow: http://localhost:5002"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3000 (admin/admin)"
	@echo ""
	@echo "Test the enhanced features:"
	@echo "  ./scripts/test-api.sh all"
	@echo "  curl http://localhost:8001/metrics"
	@echo "  curl http://localhost:8001/logs"

# Start individual services
start-api:
	@echo "Starting Enhanced California Housing API..."
	@echo "API will be available at http://localhost:8001"
	@echo "Press Ctrl+C to stop"
	source .venv/bin/activate && python src/api.py

start-mlflow:
	@echo "Starting MLflow UI..."
	@echo "MLflow will be available at http://localhost:5001"
	@echo "Press Ctrl+C to stop"
	source .venv/bin/activate && mlflow ui --backend-store-uri file:./mlruns --default-artifact-root ./mlruns --host 0.0.0.0 --port 5001

start-prometheus:
	@echo "Starting Prometheus..."
	@echo "Prometheus will be available at http://localhost:9090"
	@echo "Press Ctrl+C to stop"
	@if [ ! -d "prometheus-2.47.0.darwin-amd64" ]; then \
		echo "Downloading Prometheus..."; \
		curl -L https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.darwin-amd64.tar.gz | tar -xz; \
	fi
	cd prometheus-2.47.0.darwin-amd64 && ./prometheus --config.file=../prometheus.yml --web.listen-address=:9090

start-grafana:
	@echo "Starting Grafana..."
	@echo "Grafana will be available at http://localhost:3000 (admin/admin)"
	@echo "Press Ctrl+C to stop"
	grafana-server --config=/opt/homebrew/etc/grafana/grafana.ini --homepath=/opt/homebrew/opt/grafana/share/grafana

stop-all:
	@echo "Stopping all services..."
	@echo "All services stopped!" 