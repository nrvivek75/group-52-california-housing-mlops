.PHONY: help install test lint format clean train deploy-local deploy-remote docker-build docker-run docker-stop logs

# Default target
help:
	@echo "California Housing MLOps Project - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install       Install Python dependencies"
	@echo "  test          Run tests with pytest"
	@echo "  lint          Run linting with flake8"
	@echo "  format        Format code with black"
	@echo "  clean         Clean generated files and directories"
	@echo ""
	@echo "Model Training:"
	@echo "  train         Train all models and register best one"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run Docker container"
	@echo "  docker-stop   Stop Docker container"
	@echo "  docker-logs   View Docker container logs"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-local  Deploy locally using deployment script"
	@echo "  deploy-remote Deploy remotely from Docker Hub"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs          View application logs"
	@echo "  status        Check deployment status"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully!"

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v --cov=src --cov-report=term-missing
	@echo "✅ Tests completed!"

# Run linting
lint:
	@echo "Running linting..."
	flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "✅ Linting completed!"

# Format code
format:
	@echo "Formatting code with black..."
	black src/ tests/
	@echo "✅ Code formatting completed!"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf logs/*.log
	rm -rf models/*.pkl
	@echo "✅ Cleanup completed!"

# Train models
train:
	@echo "Training models..."
	python scripts/train_models.py
	@echo "✅ Model training completed!"

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t california-housing-mlops .
	@echo "✅ Docker image built successfully!"

docker-run:
	@echo "Running Docker container..."
	docker run -d \
		--name california-housing-api \
		--restart unless-stopped \
		-p 8000:8000 \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/mlruns:/app/mlruns \
		california-housing-mlops
	@echo "✅ Docker container started!"

docker-stop:
	@echo "Stopping Docker container..."
	docker stop california-housing-api || true
	docker rm california-housing-api || true
	@echo "✅ Docker container stopped!"

docker-logs:
	@echo "Viewing Docker container logs..."
	docker logs california-housing-api -f

# Deployment commands
deploy-local:
	@echo "Deploying locally..."
	./scripts/deploy.sh local

deploy-remote:
	@echo "Deploying remotely..."
	@read -p "Enter your Docker Hub username: " username; \
	./scripts/deploy.sh remote $$username

# Monitoring commands
logs:
	@echo "Viewing application logs..."
	tail -f logs/api.log

status:
	@echo "Checking deployment status..."
	./scripts/deploy.sh status

# Setup development environment
setup: install
	@echo "Setting up development environment..."
	mkdir -p logs models mlruns data/raw data/processed
	@echo "✅ Development environment setup completed!"

# Run all checks
check: lint test
	@echo "✅ All checks passed!"

# Full development workflow
dev: setup check
	@echo "✅ Development environment ready!"

# Production deployment
prod: docker-build docker-run
	@echo "✅ Production deployment completed!"

# Quick start
start: setup train docker-run
	@echo "✅ Quick start completed! API running at http://localhost:8000"

# Enhanced MLOps Stack (without Docker)
start-api:
	@echo "Starting Enhanced California Housing API..."
	@echo "API will be available at http://localhost:8001"
	@echo "Press Ctrl+C to stop"
	python src/api.py

start-mlflow:
	@echo "Starting MLflow UI..."
	@echo "MLflow will be available at http://localhost:5001"
	@echo "Press Ctrl+C to stop"
	mlflow ui --backend-store-uri file:./mlruns --default-artifact-root ./mlruns --host 0.0.0.0 --port 5001

start-prometheus:
	@echo "Starting Prometheus..."
	@echo "Prometheus will be available at http://localhost:9090"
	@echo "Press Ctrl+C to stop"
	@if [ ! -f "prometheus-2.47.0.darwin-amd64/prometheus" ]; then \
		echo "Downloading Prometheus..."; \
		curl -LO https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.darwin-amd64.tar.gz; \
		tar -xzf prometheus-2.47.0.darwin-amd64.tar.gz; \
	fi
	cd prometheus-2.47.0.darwin-amd64 && ./prometheus --config.file=$(PWD)/prometheus.yml --web.listen-address=:9090

start-grafana:
	@echo "Starting Grafana..."
	@echo "Grafana will be available at http://localhost:3000 (admin/admin)"
	@echo "Press Ctrl+C to stop"
	@if ! command -v grafana &> /dev/null; then \
		echo "Installing Grafana..."; \
		brew install grafana; \
	fi
	grafana server --config=/opt/homebrew/etc/grafana/grafana.ini --homepath=/opt/homebrew/opt/grafana/share/grafana --packaging=brew

# Start all enhanced services (in separate terminals)
start-all:
	@echo "🚀 Starting Enhanced MLOps Stack..."
	@echo ""
	@echo "📋 Open 4 terminal tabs and run these commands:"
	@echo ""
	@echo "Terminal 1 (API):"
	@echo "  make start-api"
	@echo ""
	@echo "Terminal 2 (MLflow):"
	@echo "  make start-mlflow"
	@echo ""
	@echo "Terminal 3 (Prometheus):"
	@echo "  make start-prometheus"
	@echo ""
	@echo "Terminal 4 (Grafana):"
	@echo "  make start-grafana"
	@echo ""
	@echo "🌐 Access your services:"
	@echo "  • API: http://localhost:8001"
	@echo "  • MLflow: http://localhost:5001"
	@echo "  • Prometheus: http://localhost:9090"
	@echo "  • Grafana: http://localhost:3000 (admin/admin)"
	@echo ""
	@echo "🧪 Test the enhanced features:"
	@echo "  • Input validation: POST http://localhost:8001/predict"
	@echo "  • Model retraining: POST http://localhost:8001/retrain"
	@echo "  • Performance metrics: GET http://localhost:8001/model/performance"
	@echo "  • Data drift check: GET http://localhost:8001/model/drift"
	@echo "  • Prometheus metrics: GET http://localhost:8001/metrics"

# Stop all services
stop-all:
	@echo "🛑 Stopping all services..."
	pkill -f "python.*api.py" || true
	pkill -f "mlflow" || true
	pkill -f "prometheus" || true
	pkill -f "grafana-server" || true
	@echo "✅ All services stopped!" 