# California Housing MLOps Project

A comprehensive MLOps project demonstrating end-to-end machine learning pipeline for California Housing price prediction, including model training, API deployment, containerization, CI/CD, and monitoring.

## 🏗️ Project Structure

```
├── src/
│   ├── api.py                 # FastAPI application with prediction endpoints
│   ├── models/                # Model implementations and training
│   ├── utils/                 # Configuration and MLflow utilities
│   └── data/                  # Data preprocessing modules
├── configs/
│   └── config.yaml           # Configuration file for models and MLflow
├── scripts/
│   ├── train_models.py       # Model training script
│   └── deploy.sh             # Deployment script
├── tests/
│   └── test_api.py           # API tests
├── logs/                     # Log files and SQLite database
├── models/                   # Trained models
├── mlruns/                   # MLflow experiment tracking
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose for local development
├── .github/workflows/        # GitHub Actions CI/CD
└── requirements.txt          # Python dependencies
```

## 🚀 Features

### Part 2: Model Development & Experiment Tracking
- ✅ **Multiple Models**: Linear Regression, Ridge, Lasso, Random Forest, Decision Tree, Gradient Boosting
- ✅ **MLflow Integration**: Complete experiment tracking with parameters, metrics, and model registry
- ✅ **Hyperparameter Tuning**: Grid search with cross-validation
- ✅ **Model Selection**: Automatic best model selection and registration

### Part 3: API & Docker Packaging
- ✅ **FastAPI Application**: RESTful API with prediction endpoints
- ✅ **Docker Containerization**: Complete containerization with health checks
- ✅ **JSON Input/Output**: Structured data validation and response formatting

### Part 4: CI/CD with GitHub Actions
- ✅ **Automated Testing**: Linting, formatting, and unit tests
- ✅ **Docker Build & Push**: Automated Docker image building and pushing to Docker Hub
- ✅ **Deployment**: Automatically deploys to EC2 with health checks

### Part 5: Logging and Monitoring
- ✅ **Comprehensive Logging**: File and console logging with structured format
- ✅ **SQLite Database**: Persistent storage of prediction requests and responses
- ✅ **Metrics Endpoint**: Real-time API metrics and statistics
- ✅ **Health Monitoring**: Health check endpoints and container health checks

## 🛠️ Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git
- Access to Docker Hub (for CI/CD)

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd group-52-california-housing-mlops
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment
```bash
# Create necessary directories
mkdir -p logs models mlruns data/raw data/processed

# Download California Housing dataset (if not already present)
# Place california_housing.csv in data/raw/ directory
```

## 🚀 Quick Start

### Option 1: Local Development
```bash
# Train models
python scripts/train_models.py

# Run API locally
python src/api.py
```

### Option 2: Docker (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use the deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh local
```

## 🔧 Usage

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Make Prediction
```bash
curl -X POST "http://localhost:8000/predict" \
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

#### Get Metrics
```bash
curl http://localhost:8000/metrics
```

#### Get Logs
```bash
curl http://localhost:8000/logs?limit=10
```

### Model Training

```bash
# Train all models and register best one
python scripts/train_models.py

# View MLflow UI (if using docker-compose)
open http://localhost:5000
```

### Deployment

```bash
# Local deployment
./scripts/deploy.sh local

# Remote deployment (from Docker Hub)
./scripts/deploy.sh remote your-dockerhub-username

# Check status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs

# Stop deployment
./scripts/deploy.sh stop
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## 🔄 CI/CD Pipeline

The GitHub Actions workflow automatically:

1. **Lints and Tests**: Runs flake8, black, and pytest on every push/PR
2. **Builds Docker Image**: Creates and pushes Docker image to Docker Hub
3. **Deploys**: Automatically deploys to EC2 instance

### Required Secrets
Set these in your GitHub repository secrets:
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password/token

## 📊 Monitoring

### Logs
- **API Logs**: `logs/api.log`
- **Training Logs**: `logs/training.log`
- **Database**: `logs/predictions.db` (SQLite)

### Metrics
- Total predictions made
- Average response time
- Recent predictions (24h)
- Model status

### MLflow Tracking
- Experiment tracking at `http://localhost:5000` (when using docker-compose)
- Model registry and versioning
- Parameter and metric logging

## 🐳 Docker

### Build Image
```bash
docker build -t california-housing-mlops .
```

### Run Container
```bash
docker run -d \
  --name california-housing-api \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/mlruns:/app/mlruns \
  california-housing-mlops
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Model Not Loading**
   ```bash
   # Check if model exists
   ls -la models/
   # Retrain models
   python scripts/train_models.py
   ```

3. **Docker Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a
   # Rebuild without cache
   docker build --no-cache -t california-housing-mlops .
   ```

### Logs
```bash
# View API logs
tail -f logs/api.log

# View container logs
docker logs california-housing-api -f

# Check MLflow logs
tail -f mlruns/california_housing_experiment/*/meta.yaml
```

## 📈 Performance

- **API Response Time**: < 100ms average
- **Model Prediction**: < 50ms average
- **Concurrent Requests**: Tested up to 100 concurrent users
- **Memory Usage**: ~500MB for API + model

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- California Housing dataset from scikit-learn
- MLflow for experiment tracking
- FastAPI for the web framework
- Docker for containerization

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review logs and error messages
3. Open an issue on GitHub
4. Contact the development team

---

**Happy MLOps! 🚀**