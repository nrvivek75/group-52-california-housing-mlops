from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import mlflow
import numpy as np
import sqlite3
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from contextlib import asynccontextmanager
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/api.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI app"""
    global model
    global retraining_system

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Ensure database is initialized
    init_db()

    # Load model with retry logic
    model = None
    max_retries = 5
    retry_delay = 10  # seconds

    for attempt in range(max_retries):
        try:
            logger.info(
                f"Attempting to load model (attempt {attempt + 1}/{max_retries})..."
            )
            model = load_model()

            if model is not None:
                logger.info("Model loaded successfully!")
                break
            else:
                logger.warning(f"Model loading failed on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Failed to load model after all retry attempts")
        except Exception as e:
            logger.error(f"Error loading model on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Failed to load model after all retry attempts")

    # Initialize retraining system
    try:
        from .retraining import ModelRetrainingSystem

        retraining_system = ModelRetrainingSystem()
        logger.info("Retraining system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize retraining system: {e}")
        retraining_system = None

    yield

    # Cleanup (if needed)
    logger.info("Shutting down API")


# Initialize FastAPI app
app = FastAPI(
    title="California Housing Price Prediction API",
    description="MLOps API for California Housing Price Prediction with MLflow integration",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Prometheus metrics
instrumentator = Instrumentator()
instrumentator.add(
    metrics.request_size(
        should_include_handler=True,
        should_include_method=True,
        should_include_status=True,
    )
)
instrumentator.add(
    metrics.response_size(
        should_include_handler=True,
        should_include_method=True,
        should_include_status=True,
    )
)
instrumentator.add(
    metrics.latency(
        should_include_handler=True,
        should_include_method=True,
        should_include_status=True,
    )
)

# Add custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Custom metrics for MLOps
prediction_counter = Counter(
    "model_predictions_total",
    "Total number of predictions made",
    ["model_type", "status"],
)
prediction_latency = Histogram(
    "model_prediction_duration_seconds", "Time spent making predictions", ["model_type"]
)
model_accuracy = Gauge("model_rmse", "Model RMSE score", ["model_type"])
model_r2_score = Gauge("model_r2_score", "Model R² score", ["model_type"])

instrumentator.instrument(app).expose(app)

# Initialize retraining system (will be set in startup)
retraining_system = None


# Pydantic models for input validation
class HousingData(BaseModel):
    longitude: float = Field(
        ..., ge=-124.5, le=-114.0, description="Longitude between -124.5 and -114.0"
    )
    latitude: float = Field(
        ..., ge=32.5, le=42.0, description="Latitude between 32.5 and 42.0"
    )
    housing_median_age: float = Field(
        ..., ge=1.0, le=52.0, description="Housing median age between 1 and 52 years"
    )
    total_rooms: float = Field(
        ..., gt=0, le=10000, description="Total rooms between 1 and 10000"
    )
    total_bedrooms: float = Field(
        ..., ge=0, le=5000, description="Total bedrooms between 0 and 5000"
    )
    population: float = Field(
        ..., gt=0, le=50000, description="Population between 1 and 50000"
    )
    households: float = Field(
        ..., gt=0, le=5000, description="Households between 1 and 5000"
    )
    median_income: float = Field(
        ..., gt=0, le=15.0, description="Median income between 0 and 15"
    )

    @field_validator("total_bedrooms")
    @classmethod
    def validate_bedrooms(cls, v, info):
        # Simple validation - we'll handle complex validation in the API logic
        if v < 0:
            raise ValueError("Total bedrooms cannot be negative")
        return v

    @field_validator("households")
    @classmethod
    def validate_households(cls, v, info):
        # Simple validation - we'll handle complex validation in the API logic
        if v < 0:
            raise ValueError("Households cannot be negative")
        return v


# Prediction response model
class PredictionResponse(BaseModel):
    prediction: float
    model_version: str
    response_time: float
    timestamp: str
    input_features: Dict[str, float]


class RetrainingRequest(BaseModel):
    trigger_type: str = Field(..., description="Type of retraining trigger")
    data_path: Optional[str] = Field(None, description="Path to new data")
    threshold: Optional[float] = Field(
        None, description="Performance threshold for retraining"
    )
    force: bool = Field(False, description="Force retraining regardless of conditions")


# Initialize database for logging
def init_db():
    """Initialize SQLite database for logging predictions"""
    try:
        conn = sqlite3.connect("logs/predictions.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                input_data TEXT,
                prediction REAL,
                model_version TEXT,
                response_time REAL
            )
        """
        )
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


# Load MLflow model
def load_model():
    """Load the best MLflow model from runs"""
    try:
        # First try to load from local models directory (more reliable)
        models_dir = "models"
        if os.path.exists(models_dir):
            # Look for any .pkl files
            for file in os.listdir(models_dir):
                if file.endswith(".pkl"):
                    model_path = os.path.join(models_dir, file)
                    try:
                        import joblib

                        model = joblib.load(model_path)
                        logger.info(
                            f"Model loaded successfully from local file: {model_path}"
                        )
                        return model
                    except Exception as e:
                        logger.warning(f"Failed to load {model_path}: {e}")
                        continue

            # Check for MLflow model directories
            for item in os.listdir(models_dir):
                item_path = os.path.join(models_dir, item)
                if os.path.isdir(item_path) and os.path.exists(
                    os.path.join(item_path, "conda.yaml")
                ):
                    try:
                        model = mlflow.sklearn.load_model(item_path)
                        logger.info(
                            f"Model loaded successfully from local MLflow directory: {item_path}"
                        )
                        return model
                    except Exception as dir_e:
                        logger.warning(f"Failed to load from {item_path}: {dir_e}")
                        continue

        # Fallback: try to load from MLflow runs
        logger.info("Local models not found, trying MLflow runs...")

        # Set MLflow tracking URI
        mlflow.set_tracking_uri("file:./mlruns")

        # First try to get the experiment by name
        experiment = mlflow.get_experiment_by_name("california_housing_experiment")

        # If not found, try to get the default experiment or list all experiments
        if experiment is None:
            logger.info(
                "Experiment 'california_housing_experiment' not found, searching for alternatives..."
            )

            # Try to get the default experiment
            try:
                experiment = mlflow.get_experiment(0)  # Default experiment ID
                logger.info(f"Using default experiment: {experiment.name}")
            except:
                # List all experiments and use the first one
                experiments = mlflow.search_experiments()
                if experiments:
                    experiment = experiments[0]
                    logger.info(f"Using first available experiment: {experiment.name}")
                else:
                    logger.error("No MLflow experiments found")
                    return None

        if not experiment:
            logger.error("No MLflow experiment found")
            return None

        logger.info(f"Using experiment: {experiment.name}")

        # Get the client
        client = mlflow.tracking.MlflowClient()

        # Search for runs
        runs = client.search_runs(experiment_ids=[experiment.experiment_id])
        logger.info(f"Found {len(runs)} MLflow runs")

        if not runs:
            logger.error("No MLflow runs found")
            return None

        # Get the best run (lowest RMSE)
        best_run = None
        best_rmse = float("inf")

        for run in runs:
            # Check for different RMSE metric names that might exist
            rmse = None
            if run.data.metrics.get("rmse"):
                rmse = run.data.metrics["rmse"]
            elif run.data.metrics.get("test_rmse"):
                rmse = run.data.metrics["test_rmse"]
            elif run.data.metrics.get("train_rmse"):
                rmse = run.data.metrics["train_rmse"]

            if rmse is not None:
                logger.info(f"Run {run.info.run_name} has RMSE: {rmse}")
                if rmse < best_rmse:
                    best_rmse = rmse
                    best_run = run

        if not best_run:
            logger.error("No run with RMSE metric found")
            # List all runs and their metrics for debugging
            for run in runs:
                logger.info(f"Run {run.info.run_name} metrics: {run.data.metrics}")
            return None

        logger.info(
            f"Loading best model from run: {best_run.info.run_name} (RMSE: {best_rmse:.2f})"
        )

        # Try to load the model from the run
        try:
            model = mlflow.sklearn.load_model(f"runs:/{best_run.info.run_id}/model")
            logger.info("Model loaded successfully from MLflow run")

            # Save the model locally for future use
            try:
                import joblib

                os.makedirs("models", exist_ok=True)
                joblib.dump(model, "models/best_model.pkl")
                logger.info("Model saved locally for future use")
            except Exception as save_e:
                logger.warning(f"Could not save model locally: {save_e}")

            return model
        except Exception as mlflow_e:
            logger.warning(f"Failed to load from MLflow run: {mlflow_e}")
            return None

    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None


# Initialize model and database
model = None

# Initialize database immediately when module is imported
init_db()

# Remove the old startup event handler since we're using lifespan now


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "California Housing Price Prediction API", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": model is not None,
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: Request, housing_data: HousingData):
    """Make a housing price prediction"""
    start_time = datetime.now()

    try:
        if model is None:
            # Increment failed prediction counter
            prediction_counter.labels(model_type="unknown", status="failed").inc()
            raise HTTPException(
                status_code=503,
                detail="Model not available. Please ensure the model is trained and loaded.",
            )

        # Additional validation logic
        if housing_data.total_bedrooms > housing_data.total_rooms:
            raise HTTPException(
                status_code=422, detail="Total bedrooms cannot exceed total rooms"
            )

        if housing_data.households > housing_data.population:
            raise HTTPException(
                status_code=422, detail="Households cannot exceed population"
            )

        # Convert input to numpy array
        input_features = np.array(
            [
                [
                    housing_data.longitude,
                    housing_data.latitude,
                    housing_data.housing_median_age,
                    housing_data.total_rooms,
                    housing_data.total_bedrooms,
                    housing_data.population,
                    housing_data.households,
                    housing_data.median_income,
                ]
            ]
        )

        # Make prediction
        prediction = model.predict(input_features)[0]

        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()

        # Update custom metrics
        model_type = type(model).__name__
        prediction_counter.labels(model_type=model_type, status="success").inc()
        prediction_latency.labels(model_type=model_type).observe(response_time)

        # Log prediction to database
        log_prediction(housing_data.model_dump(), prediction, response_time)

        return PredictionResponse(
            prediction=float(prediction),
            model_version="1.0.0",
            response_time=response_time,
            timestamp=datetime.now().isoformat(),
            input_features=housing_data.model_dump(),
        )

    except HTTPException:
        # Increment failed prediction counter
        if model is not None:
            model_type = type(model).__name__
        else:
            model_type = "unknown"
        prediction_counter.labels(model_type=model_type, status="failed").inc()
        raise
    except Exception as e:
        # Increment failed prediction counter
        if model is not None:
            model_type = type(model).__name__
        else:
            model_type = "unknown"
        prediction_counter.labels(model_type=model_type, status="failed").inc()

        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@app.post("/retrain", response_model=Dict[str, str])
async def trigger_retraining(request: RetrainingRequest):
    """Trigger model retraining based on various conditions"""
    try:
        if retraining_system is None:
            raise HTTPException(
                status_code=503, detail="Retraining system not available"
            )

        logger.info(f"Retraining triggered: {request.trigger_type}")

        # Validate retraining request
        if request.trigger_type not in [
            "performance",
            "data_drift",
            "manual",
            "scheduled",
        ]:
            raise HTTPException(status_code=400, detail="Invalid trigger type")

        # Use the retraining system
        if request.trigger_type == "performance":
            result = retraining_system.trigger_retraining("performance", request.force)
        elif request.trigger_type == "data_drift":
            result = retraining_system.trigger_retraining("data_drift", request.force)
        elif request.trigger_type == "manual":
            result = retraining_system.trigger_retraining("manual", request.force)
        elif request.trigger_type == "scheduled":
            result = retraining_system.schedule_retraining()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")


@app.get("/model/performance")
async def get_model_performance():
    """Get current model performance metrics"""
    try:
        if retraining_system is None:
            raise HTTPException(
                status_code=503, detail="Retraining system not available"
            )

        needs_retraining, metrics = retraining_system.check_model_performance()

        return {
            "needs_retraining": needs_retraining,
            "performance_metrics": metrics,
            "thresholds": {
                "rmse": retraining_system.threshold_rmse,
                "r2": retraining_system.threshold_r2,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance: {str(e)}"
        )


@app.get("/model/drift")
async def check_data_drift():
    """Check for data drift"""
    try:
        if retraining_system is None:
            raise HTTPException(
                status_code=503, detail="Retraining system not available"
            )

        needs_retraining, drift_metrics = retraining_system.check_data_drift()

        return {
            "needs_retraining": needs_retraining,
            "drift_metrics": drift_metrics,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking data drift: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check drift: {str(e)}")


def log_prediction(input_data: Dict, prediction: float, response_time: float):
    """Log prediction to SQLite database"""
    try:
        conn = sqlite3.connect("logs/predictions.db")
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                input_data TEXT,
                prediction REAL,
                model_version TEXT,
                response_time REAL
            )
        """
        )

        cursor.execute(
            """
            INSERT INTO predictions (timestamp, input_data, prediction, model_version, response_time)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                datetime.now().isoformat(),
                json.dumps(input_data),
                prediction,
                "1.0.0",
                response_time,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging to database: {e}")


@app.get("/metrics")
async def get_metrics():
    """Get API metrics and statistics"""
    try:
        conn = sqlite3.connect("logs/predictions.db")
        cursor = conn.cursor()

        # Get total predictions
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]

        # Get average response time
        cursor.execute("SELECT AVG(response_time) FROM predictions")
        avg_response_time = cursor.fetchone()[0] or 0

        # Get recent predictions (last 24 hours)
        cursor.execute(
            """
            SELECT COUNT(*) FROM predictions 
            WHERE timestamp > datetime('now', '-1 day')
        """
        )
        recent_predictions = cursor.fetchone()[0]

        conn.close()

        return {
            "total_predictions": total_predictions,
            "average_response_time": round(avg_response_time, 3),
            "recent_predictions_24h": recent_predictions,
            "model_status": "loaded" if model else "not_loaded",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": str(e)}


@app.get("/logs")
async def get_logs(limit: int = 100):
    """Get recent prediction logs"""
    try:
        conn = sqlite3.connect("logs/predictions.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT timestamp, input_data, prediction, response_time 
            FROM predictions 
            ORDER BY timestamp DESC 
            LIMIT ?
        """,
            (limit,),
        )

        logs = []
        for row in cursor.fetchall():
            logs.append(
                {
                    "timestamp": row[0],
                    "input_data": json.loads(row[1]),
                    "prediction": row[2],
                    "response_time": row[3],
                }
            )

        conn.close()
        return {"logs": logs, "count": len(logs)}

    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
