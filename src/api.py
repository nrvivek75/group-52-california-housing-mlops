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
from pydantic import BaseModel, Field, validator
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="California Housing Price Prediction API",
    description="MLOps API for California Housing Price Prediction with MLflow integration",
    version="2.0.0"
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
Instrumentator().instrument(app).expose(app)

# Initialize retraining system (will be set in startup)
retraining_system = None

# Pydantic models for input validation
class HousingData(BaseModel):
    longitude: float = Field(..., ge=-124.5, le=-114.0, description="Longitude between -124.5 and -114.0")
    latitude: float = Field(..., ge=32.5, le=42.0, description="Latitude between 32.5 and 42.0")
    housing_median_age: float = Field(..., ge=1.0, le=52.0, description="Housing median age between 1 and 52 years")
    total_rooms: float = Field(..., gt=0, le=10000, description="Total rooms between 1 and 10000")
    total_bedrooms: float = Field(..., ge=0, le=5000, description="Total bedrooms between 0 and 5000")
    population: float = Field(..., gt=0, le=50000, description="Population between 1 and 50000")
    households: float = Field(..., gt=0, le=5000, description="Households between 1 and 5000")
    median_income: float = Field(..., gt=0, le=15.0, description="Median income between 0 and 15")

    @validator('total_bedrooms')
    def validate_bedrooms(cls, v, values):
        if 'total_rooms' in values and v > values['total_rooms']:
            raise ValueError('Total bedrooms cannot exceed total rooms')
        return v

    @validator('households')
    def validate_households(cls, v, values):
        if 'population' in values and v > values['population']:
            raise ValueError('Households cannot exceed population')
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
    threshold: Optional[float] = Field(None, description="Performance threshold for retraining")
    force: bool = Field(False, description="Force retraining regardless of conditions")

# Initialize database for logging
def init_db():
    """Initialize SQLite database for logging predictions"""
    try:
        conn = sqlite3.connect('logs/predictions.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                input_data TEXT,
                prediction REAL,
                model_version TEXT,
                response_time REAL
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

# Load MLflow model
def load_model():
    """Load the registered MLflow model"""
    try:
        model = mlflow.pyfunc.load_model("models:/california_housing_best_model/Production")
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

# Initialize model and database
model = None

# Initialize database immediately when module is imported
init_db()

@app.on_event("startup")
async def startup_event():
    global model
    global retraining_system
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Ensure database is initialized
    init_db()
    
    # Load model
    model = load_model()
    
    if model is None:
        logger.error("Failed to load model on startup")

    # Initialize retraining system
    from retraining import retraining_system
    retraining_system = retraining_system.RetrainingSystem()
    logger.info("Retraining system initialized")

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
        "model_loaded": model is not None
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: Request, housing_data: HousingData):
    """Make a housing price prediction"""
    start_time = datetime.now()
    
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        # Convert input to numpy array
        input_features = np.array([[
            housing_data.longitude,
            housing_data.latitude,
            housing_data.housing_median_age,
            housing_data.total_rooms,
            housing_data.total_bedrooms,
            housing_data.population,
            housing_data.households,
            housing_data.median_income
        ]])
        
        # Make prediction
        prediction = model.predict(input_features)[0]
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Log prediction to database
        log_prediction(housing_data.model_dump(), prediction, response_time)
        
        return PredictionResponse(
            prediction=float(prediction),
            model_version="1.0.0",
            response_time=response_time,
            timestamp=datetime.now().isoformat(),
            input_features=housing_data.model_dump()
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/retrain", response_model=Dict[str, str])
async def trigger_retraining(request: RetrainingRequest):
    """Trigger model retraining based on various conditions"""
    try:
        logger.info(f"Retraining triggered: {request.trigger_type}")
        
        # Validate retraining request
        if request.trigger_type not in ["performance", "data_drift", "manual", "scheduled"]:
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
        
    except Exception as e:
        logger.error(f"Error triggering retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

@app.get("/model/performance")
async def get_model_performance():
    """Get current model performance metrics"""
    try:
        needs_retraining, metrics = retraining_system.check_model_performance()
        
        return {
            "needs_retraining": needs_retraining,
            "performance_metrics": metrics,
            "thresholds": {
                "rmse": retraining_system.threshold_rmse,
                "r2": retraining_system.threshold_r2
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")

@app.get("/model/drift")
async def check_data_drift():
    """Check for data drift"""
    try:
        needs_retraining, drift_metrics = retraining_system.check_data_drift()
        
        return {
            "needs_retraining": needs_retraining,
            "drift_metrics": drift_metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking data drift: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check drift: {str(e)}")

def log_prediction(input_data: Dict, prediction: float, response_time: float):
    """Log prediction to SQLite database"""
    try:
        conn = sqlite3.connect('logs/predictions.db')
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                input_data TEXT,
                prediction REAL,
                model_version TEXT,
                response_time REAL
            )
        ''')
        
        cursor.execute('''
            INSERT INTO predictions (timestamp, input_data, prediction, model_version, response_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            json.dumps(input_data),
            prediction,
            "1.0.0",
            response_time
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging to database: {e}")

@app.get("/metrics")
async def get_metrics():
    """Get API metrics and statistics"""
    try:
        conn = sqlite3.connect('logs/predictions.db')
        cursor = conn.cursor()
        
        # Get total predictions
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]
        
        # Get average response time
        cursor.execute("SELECT AVG(response_time) FROM predictions")
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Get recent predictions (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE timestamp > datetime('now', '-1 day')
        """)
        recent_predictions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_predictions": total_predictions,
            "average_response_time": round(avg_response_time, 3),
            "recent_predictions_24h": recent_predictions,
            "model_status": "loaded" if model else "not_loaded",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": str(e)}

@app.get("/logs")
async def get_logs(limit: int = 100):
    """Get recent prediction logs"""
    try:
        conn = sqlite3.connect('logs/predictions.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, input_data, prediction, response_time 
            FROM predictions 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "timestamp": row[0],
                "input_data": json.loads(row[1]),
                "prediction": row[2],
                "response_time": row[3]
            })
        
        conn.close()
        return {"logs": logs, "count": len(logs)}
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 