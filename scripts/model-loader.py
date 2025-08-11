#!/usr/bin/env python3
"""
Model Loader Script for MLOps
Handles model loading and validation for production deployment
"""

import os
import sys
import mlflow
from mlflow.tracking import MlflowClient
import joblib
import shutil

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"[SUCCESS] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def load_best_model():
    """Load the best model from MLflow for production use"""
    log_info("Starting model loading for production...")
    
    try:
        # Change to app directory
        os.chdir("/app")
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri('file:./mlruns')
        
        # Get the experiment
        experiment = mlflow.get_experiment_by_name('california_housing_experiment')
        if not experiment:
            log_error("MLflow experiment not found!")
            return False
        
        log_info(f"Found experiment: {experiment.name}")
        
        # Get the client
        client = MlflowClient()
        
        # Search for runs
        runs = client.search_runs(experiment_ids=[experiment.experiment_id])
        log_info(f"Found {len(runs)} MLflow runs")
        
        if not runs:
            log_error("No MLflow runs found!")
            return False
        
        # Get the best run (lowest RMSE)
        best_run = None
        best_rmse = float('inf')
        
        for run in runs:
            if run.data.metrics.get('rmse'):
                rmse = run.data.metrics['rmse']
                if rmse < best_rmse:
                    best_rmse = rmse
                    best_run = run
        
        if not best_run:
            log_error("No run with RMSE metric found!")
            return False
        
        log_info(f"Best run: {best_run.info.run_name} (RMSE: {best_rmse:.2f})")
        
        # Download the model
        log_info("Downloading model...")
        model_path = mlflow.artifacts.download_artifacts(
            run_id=best_run.info.run_id,
            artifact_path="model"
        )
        
        log_info(f"Model downloaded to: {model_path}")
        
        # Copy model to models directory
        models_dir = "/app/models"
        os.makedirs(models_dir, exist_ok=True)
        
        # Copy the entire model directory
        target_model_dir = os.path.join(models_dir, "best_model")
        if os.path.exists(target_model_dir):
            shutil.rmtree(target_model_dir)
        
        shutil.copytree(model_path, target_model_dir)
        log_success(f"Model copied to: {target_model_dir}")
        
        # Create a symlink for the API to find
        model_link = os.path.join(models_dir, "current_model")
        if os.path.exists(model_link):
            os.remove(model_link)
        
        os.symlink(target_model_dir, model_link)
        log_success(f"Model symlink created: {model_link}")
        
        # Test loading the model
        log_info("Testing model loading...")
        try:
            model = mlflow.sklearn.load_model(target_model_dir)
            log_success(f"Model loaded successfully: {type(model).__name__}")
            
            # Test prediction
            import numpy as np
            test_data = np.array([[-118.25, 34.05, 35.0, 1500.0, 200.0, 500.0, 150.0, 7.5]])
            prediction = model.predict(test_data)
            log_success(f"Test prediction successful: ${prediction[0]:,.2f}")
            
            return True
            
        except Exception as e:
            log_error(f"Model loading test failed: {e}")
            return False
        
    except Exception as e:
        log_error(f"Model loading failed: {e}")
        return False

def main():
    """Main function"""
    if load_best_model():
        log_success("Model loading completed successfully!")
        return True
    else:
        log_error("Model loading failed!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 