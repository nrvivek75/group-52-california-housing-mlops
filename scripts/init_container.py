#!/usr/bin/env python3
"""
Container Initialization Script for MLOps
This script ensures the container has all necessary data and models
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"[SUCCESS] {message}")

def log_warning(message):
    print(f"[WARNING] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def ensure_directories():
    """Ensure all necessary directories exist"""
    log_info("Creating necessary directories...")
    directories = [
        "/app/logs",
        "/app/mlruns", 
        "/app/models",
        "/app/data",
        "/app/data/raw",
        "/app/data/processed"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    log_success("Directories created")

def check_and_create_data():
    """Check if data exists, create if not"""
    log_info("Checking for data files...")
    
    data_file = Path("/app/data/raw/california_housing.csv")
    if not data_file.exists():
        log_info("Data file not found, creating sample data...")
        
        # Create sample California housing data
        import pandas as pd
        import numpy as np
        
        # Generate synthetic California housing data
        np.random.seed(42)
        n_samples = 1000
        
        data = {
            'longitude': np.random.uniform(-124.5, -114.0, n_samples),
            'latitude': np.random.uniform(32.5, 42.0, n_samples),
            'housing_median_age': np.random.uniform(1.0, 52.0, n_samples),
            'total_rooms': np.random.uniform(1.0, 10000.0, n_samples),
            'total_bedrooms': np.random.uniform(0.0, 5000.0, n_samples),
            'population': np.random.uniform(1.0, 50000.0, n_samples),
            'households': np.random.uniform(1.0, 5000.0, n_samples),
            'median_income': np.random.uniform(0.1, 15.0, n_samples),
            'median_house_value': np.random.uniform(50000, 500000, n_samples)
        }
        
        df = pd.DataFrame(data)
        df.to_csv(data_file, index=False)
        log_success(f"Created sample data with {n_samples} records")
    else:
        log_success("Data file already exists")

def train_models():
    """Train models to create MLflow runs"""
    log_info("Training models to create MLflow runs...")
    
    try:
        # Check if we have the training script
        training_script = Path("/app/scripts/train_models.py")
        if not training_script.exists():
            log_error("Training script not found")
            return False
        
        # Run training script
        log_info("Starting model training...")
        result = subprocess.run(
            ["python", "scripts/train_models.py"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode == 0:
            log_success("Models trained successfully")
            return True
        else:
            log_error(f"Training failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        log_error("Training timed out")
        return False
    except Exception as e:
        log_error(f"Training failed: {e}")
        return False

def initialize_mlflow():
    """Initialize MLflow experiment"""
    log_info("Initializing MLflow...")
    
    try:
        import mlflow
        
        # Set tracking URI
        mlflow.set_tracking_uri('file:./mlruns')
        
        # Create experiment if it doesn't exist
        experiment_name = 'california_housing_experiment'
        experiment = mlflow.get_experiment_by_name(experiment_name)
        
        if experiment is None:
            mlflow.create_experiment(experiment_name)
            log_success(f"Created MLflow experiment: {experiment_name}")
        else:
            log_success(f"MLflow experiment exists: {experiment_name}")
            
        # Check if we have runs
        client = mlflow.tracking.MlflowClient()
        runs = client.search_runs(experiment_ids=[experiment.experiment_id])
        log_info(f"Found {len(runs)} MLflow runs")
        
        return True
            
    except Exception as e:
        log_error(f"MLflow initialization failed: {e}")
        return False

def create_sample_mlflow_runs():
    """Create sample MLflow runs if none exist"""
    log_info("Checking for MLflow runs...")
    
    try:
        import mlflow
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error
        import pandas as pd
        import numpy as np
        
        # Set tracking URI
        mlflow.set_tracking_uri('file:./mlruns')
        mlflow.set_experiment('california_housing_experiment')
        
        # Load or create data
        data_file = Path("/app/data/raw/california_housing.csv")
        if data_file.exists():
            data = pd.read_csv(data_file)
        else:
            log_warning("No data file found, creating sample runs with synthetic data")
            return False
        
        # Prepare features and target
        feature_cols = ['longitude', 'latitude', 'housing_median_age', 'total_rooms', 
                       'total_bedrooms', 'population', 'households', 'median_income']
        X = data[feature_cols].values
        y = data['median_house_value'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Create multiple runs with different models
        models = [
            ("RandomForest", RandomForestRegressor(n_estimators=100, random_state=42)),
            ("RandomForest_200", RandomForestRegressor(n_estimators=200, random_state=42)),
            ("RandomForest_300", RandomForestRegressor(n_estimators=300, random_state=42))
        ]
        
        for model_name, model in models:
            with mlflow.start_run(run_name=model_name):
                # Log parameters
                mlflow.log_param("n_estimators", model.n_estimators)
                mlflow.log_param("random_state", model.random_state)
                
                # Train model
                model.fit(X_train, y_train)
                
                # Make predictions
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                
                # Log metrics
                mlflow.log_metric("mse", mse)
                mlflow.log_metric("rmse", rmse)
                
                # Log model
                mlflow.sklearn.log_model(model, "model")
                
                log_info(f"Created MLflow run: {model_name} (RMSE: {rmse:.2f})")
        
        log_success(f"Created {len(models)} sample MLflow runs")
        return True
        
    except Exception as e:
        log_error(f"Failed to create sample MLflow runs: {e}")
        return False

def main():
    """Main initialization function"""
    log_info("Starting container initialization...")
    
    try:
        # Change to app directory
        os.chdir("/app")
        
        # Run initialization steps
        ensure_directories()
        check_and_create_data()
        
        # Try to train models first
        if not train_models():
            log_warning("Model training failed, creating sample runs instead")
            create_sample_mlflow_runs()
        
        # Initialize MLflow
        initialize_mlflow()
        
        log_success("Container initialization completed successfully!")
        
    except Exception as e:
        log_error(f"Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 