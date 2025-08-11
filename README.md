# California Housing MLOps Project

A comprehensive MLOps pipeline for California Housing Price Prediction, featuring model training, experiment tracking, API deployment, monitoring, and automated CI/CD.

## Project Structure

```
group-52-california-housing-mlops/
├── src/                    # Source code
│   ├── api.py             # FastAPI application
│   ├── models.py          # ML model definitions
│   ├── data_processing.py # Data preprocessing
│   └── retraining.py      # Model retraining system
├── tests/                  # Unit tests
├── configs/                # Configuration files
├── scripts/                # Utility scripts
├── logs/                   # Application logs
├── models/                 # Trained models
├── mlruns/                 # MLflow experiment tracking
├── data/                   # Dataset files
├── .github/workflows/      # CI/CD pipelines
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Multi-service orchestration
└── requirements.txt        # Python dependencies
```

## Features

### Model Development & Experiment Tracking
- **Multiple Models**: Linear Regression, Ridge, Lasso, Random Forest, Decision Tree, Gradient Boosting
- **MLflow Integration**: Complete experiment tracking with parameters, metrics, and model registry
- **Hyperparameter Tuning**: Grid search with cross-validation
- **Model Selection**: Automatic best model selection and registration

### API & Deployment
- **FastAPI Application**: RESTful API with prediction endpoints
- **Docker Containerization**: Complete containerization with health checks
- **JSON Input/Output**: Structured data validation and response formatting

### CI/CD Pipeline
- **Automated Testing**: Linting, formatting, and unit tests
- **Docker Build & Push**: Automated Docker image building and pushing to Docker Hub
- **Deployment**: Local deployment with health checks

### Monitoring & Logging
- **Comprehensive Logging**: File and console logging with structured format
- **SQLite Database**: Persistent storage of prediction requests and responses
- **Metrics Endpoint**: Real-time API metrics and statistics
- **Health Monitoring**: Health check endpoints and container health checks

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- MLflow
- FastAPI
- Scikit-learn
- Pandas
- NumPy

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/group-52-california-housing-mlops.git
   cd group-52-california-housing-mlops
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment**
   ```bash
   make setup-env
   ```

## Quick Start

### Option 1: All-in-One Docker Image (Recommended)
```bash
# Build and start all services
./scripts/start.sh start

# Access your services
# API: http://localhost:8001
# MLflow: http://localhost:5002
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### Option 2: Individual Services
```bash
# Start enhanced MLOps stack
make start-enhanced

# This will show you commands to run in separate terminals
```

### Option 3: Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Usage

### Training Models
```bash
# Train all models and register best one
make train

# Or run directly
python scripts/train_models.py
```

### API Endpoints
- **Health Check**: `GET /health`
- **Prediction**: `POST /predict`
- **Metrics**: `GET /metrics`
- **Logs**: `GET /logs`
- **Model Performance**: `GET /model/performance`
- **Data Drift**: `GET /model/drift`
- **Retraining**: `POST /retrain`

### Example Prediction Request
```bash
curl -X POST "http://localhost:8001/predict" \
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

## Testing

### Run All Tests
```bash
make test
```

### Run Specific Tests
```bash
# Test API endpoints
./scripts/test-api.sh all

# Test specific endpoint
./scripts/test-api.sh prediction
```

### Code Quality
```bash
# Linting
make lint

# Formatting
make format

# All checks
make check-env
```

## CI/CD Pipeline

The project includes automated CI/CD with GitHub Actions:

1. **Lint & Test**: Code quality checks and unit tests
2. **Build**: Docker image building
3. **Push**: Automatic push to Docker Hub
4. **Deploy**: Local deployment instructions

### Required GitHub Secrets
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub access token

## Monitoring

### Prometheus Metrics
- API request rates
- Response times
- Error rates
- Custom business metrics

### Grafana Dashboards
- Real-time API performance
- Model prediction statistics
- System health monitoring

### MLflow Tracking
- Experiment parameters
- Model performance metrics
- Model versioning
- Artifact storage

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   lsof -i :8001
   docker stop $(docker ps -q)
   ```

2. **Container Won't Start**
   ```bash
   docker logs mlops-all-in-one
   docker stats mlops-all-in-one
   ```

3. **Services Not Responding**
   ```bash
   curl http://localhost:8001/health
   docker ps -a
   ```

### Debug Commands
```bash
# Check container status
docker ps -a

# View logs
docker logs -f mlops-all-in-one

# Enter container
docker exec -it mlops-all-in-one bash

# Check supervisor status
supervisorctl status
```

## Performance

### Resource Requirements
- **Minimum**: 2GB RAM, 2 CPU cores
- **Recommended**: 4GB RAM, 4 CPU cores
- **Storage**: 5GB+ for models and data

### Optimization Tips
- Use volume mounts for persistent data
- Monitor resource usage with `docker stats`
- Adjust supervisor restart policies if needed
- Consider resource limits for production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- California Housing Dataset
- MLflow for experiment tracking
- FastAPI for the web framework
- Docker for containerization
- Prometheus and Grafana for monitoring

---

**Happy MLOps!**