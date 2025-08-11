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

def copy_trained_models():
    """Copy trained models if they exist"""
    log_info("Checking for trained models...")
    
    # Check if we have models locally
    local_models = Path("models")
    if local_models.exists() and any(local_models.glob("*.pkl")):
        log_info("Found local models, copying to container...")
        
        # Copy models to container
        container_models = Path("/app/models")
        if container_models.exists():
            shutil.rmtree(container_models)
        
        shutil.copytree(local_models, container_models)
        log_success("Models copied to container")
    else:
        log_warning("No local models found")

def copy_mlflow_data():
    """Copy MLflow data if it exists"""
    log_info("Checking for MLflow data...")
    
    # Check if we have MLflow data locally
    local_mlruns = Path("mlruns")
    if local_mlruns.exists() and any(local_mlruns.iterdir()):
        log_info("Found local MLflow data, copying to container...")
        
        # Copy MLflow data to container
        container_mlruns = Path("/app/mlruns")
        if container_mlruns.exists():
            shutil.rmtree(container_mlruns)
        
        shutil.copytree(local_mlruns, container_mlruns)
        log_success("MLflow data copied to container")
    else:
        log_warning("No local MLflow data found")

def copy_data_files():
    """Copy data files if they exist"""
    log_info("Checking for data files...")
    
    # Check if we have data locally
    local_data = Path("data")
    if local_data.exists():
        log_info("Found local data, copying to container...")
        
        # Copy data to container
        container_data = Path("/app/data")
        if container_data.exists():
            shutil.rmtree(container_data)
        
        shutil.copytree(local_data, container_data)
        log_success("Data files copied to container")
    else:
        log_warning("No local data found")

def train_models_if_needed():
    """Train models if none exist"""
    log_info("Checking if models need to be trained...")
    
    container_models = Path("/app/models")
    container_mlruns = Path("/app/mlruns")
    
    # Check if we have models and MLflow data
    has_models = container_models.exists() and any(container_models.glob("*.pkl"))
    has_mlflow_data = container_mlruns.exists() and any(container_mlruns.iterdir())
    
    if not has_models or not has_mlflow_data:
        log_info("Training models...")
        try:
            # Run training script
            result = subprocess.run(
                ["python", "scripts/train_models.py"],
                cwd="/app",
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                log_success("Models trained successfully")
            else:
                log_error(f"Training failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            log_error("Training timed out")
        except Exception as e:
            log_error(f"Training failed: {e}")
    else:
        log_success("Models and MLflow data already exist")

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
            
    except Exception as e:
        log_error(f"MLflow initialization failed: {e}")

def main():
    """Main initialization function"""
    log_info("Starting container initialization...")
    
    try:
        # Change to app directory
        os.chdir("/app")
        
        # Run initialization steps
        ensure_directories()
        copy_trained_models()
        copy_mlflow_data()
        copy_data_files()
        train_models_if_needed()
        initialize_mlflow()
        
        log_success("Container initialization completed successfully!")
        
    except Exception as e:
        log_error(f"Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 