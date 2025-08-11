import pytest
import json
import sqlite3
from fastapi.testclient import TestClient
from src.api import app, log_prediction
from src.retraining import retraining_system

client = TestClient(app)

# Sample housing data for testing
sample_housing_data = {
    "longitude": -122.23,
    "latitude": 37.88,
    "housing_median_age": 41.0,
    "total_rooms": 880.0,
    "total_bedrooms": 129.0,
    "population": 322.0,
    "households": 126.0,
    "median_income": 8.3252
}

# Invalid data for testing validation
invalid_housing_data = {
    "longitude": -200.0,  # Invalid longitude
    "latitude": 50.0,     # Invalid latitude
    "housing_median_age": 100.0,  # Invalid age
    "total_rooms": -10.0,  # Invalid rooms
    "total_bedrooms": 1000.0,  # Invalid bedrooms
    "population": 0.0,     # Invalid population
    "households": 1000.0,  # Invalid households
    "median_income": -5.0  # Invalid income
}

@pytest.fixture
def setup_test_db():
    """Setup test database"""
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Initialize database
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
    
    yield
    
    # Cleanup
    import os
    if os.path.exists('logs/predictions.db'):
        os.remove('logs/predictions.db')

class TestInputValidation:
    """Test input validation functionality"""
    
    def test_valid_housing_data(self):
        """Test that valid housing data passes validation"""
        response = client.post("/predict", json=sample_housing_data)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "model_version" in data
        assert "response_time" in data
    
    def test_invalid_longitude(self):
        """Test validation of longitude field"""
        invalid_data = sample_housing_data.copy()
        invalid_data["longitude"] = -200.0  # Out of range
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_latitude(self):
        """Test validation of latitude field"""
        invalid_data = sample_housing_data.copy()
        invalid_data["latitude"] = 50.0  # Out of range
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_rooms(self):
        """Test validation of total_rooms field"""
        invalid_data = sample_housing_data.copy()
        invalid_data["total_rooms"] = -10.0  # Negative value
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_bedrooms_exceed_rooms(self):
        """Test that bedrooms cannot exceed total rooms"""
        invalid_data = sample_housing_data.copy()
        invalid_data["total_rooms"] = 100.0
        invalid_data["total_bedrooms"] = 150.0  # More bedrooms than rooms
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_households_exceed_population(self):
        """Test that households cannot exceed population"""
        invalid_data = sample_housing_data.copy()
        invalid_data["population"] = 50.0
        invalid_data["households"] = 100.0  # More households than population
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 422  # Validation error

class TestRetrainingEndpoints:
    """Test retraining functionality"""
    
    def test_trigger_retraining_manual(self):
        """Test manual retraining trigger"""
        response = client.post("/retrain", json={
            "trigger_type": "manual",
            "force": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "trigger_type" in data
        assert data["trigger_type"] == "manual"
    
    def test_trigger_retraining_performance(self):
        """Test performance-based retraining trigger"""
        response = client.post("/retrain", json={
            "trigger_type": "performance",
            "threshold": 0.6
        })
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "trigger_type" in data
        assert data["trigger_type"] == "performance"
    
    def test_trigger_retraining_data_drift(self):
        """Test data drift retraining trigger"""
        response = client.post("/retrain", json={
            "trigger_type": "data_drift"
        })
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "trigger_type" in data
        assert data["trigger_type"] == "data_drift"
    
    def test_trigger_retraining_scheduled(self):
        """Test scheduled retraining trigger"""
        response = client.post("/retrain", json={
            "trigger_type": "scheduled"
        })
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "trigger_type" in data
        assert data["trigger_type"] == "scheduled"
    
    def test_invalid_trigger_type(self):
        """Test invalid retraining trigger type"""
        response = client.post("/retrain", json={
            "trigger_type": "invalid_type"
        })
        assert response.status_code == 400
        assert "Invalid trigger type" in response.json()["detail"]
    
    def test_get_model_performance(self):
        """Test getting model performance metrics"""
        response = client.get("/model/performance")
        assert response.status_code == 200
        data = response.json()
        assert "needs_retraining" in data
        assert "thresholds" in data
        assert "rmse" in data["thresholds"]
        assert "r2" in data["thresholds"]
    
    def test_check_data_drift(self):
        """Test checking for data drift"""
        response = client.get("/model/drift")
        assert response.status_code == 200
        data = response.json()
        assert "needs_retraining" in data
        assert "drift_metrics" in data

class TestDatabaseLogging:
    """Test database logging functionality"""
    
    def test_prediction_logging(self, setup_test_db):
        """Test that predictions are logged to database"""
        # Log a test prediction
        log_prediction(sample_housing_data, 2.5, 0.1)
        
        # Check if it was logged
        conn = sqlite3.connect('logs/predictions.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM predictions")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count >= 1  # At least 1 record should exist

class TestAPIEndpoints:
    """Test basic API functionality"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Should return Prometheus metrics
        assert "http_requests_total" in response.text
    
    def test_logs_endpoint(self):
        """Test logs endpoint"""
        response = client.get("/logs")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
    
    def test_prediction_endpoint(self):
        """Test prediction endpoint with valid data"""
        response = client.post("/predict", json=sample_housing_data)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "model_version" in data
        assert "response_time" in data
        assert "timestamp" in data
        assert "input_features" in data

class TestErrorHandling:
    """Test error handling"""
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        incomplete_data = {
            "longitude": -122.23,
            "latitude": 37.88
            # Missing other required fields
        }
        
        response = client.post("/predict", json=incomplete_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_data_types(self):
        """Test handling of invalid data types"""
        invalid_types_data = sample_housing_data.copy()
        invalid_types_data["longitude"] = "invalid_string"  # Should be float
        
        response = client.post("/predict", json=invalid_types_data)
        assert response.status_code == 422  # Validation error 