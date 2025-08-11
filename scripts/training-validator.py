#!/usr/bin/env python3
"""
Training Validator for MLOps
Validates training results and model quality for production deployment
"""

import os
import sys
import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
import numpy as np
from pathlib import Path

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"[SUCCESS] {message}")

def log_warning(message):
    print(f"[WARNING] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def validate_training_results():
    """Validate that training produced expected results"""
    log_info("Validating training results...")
    
    try:
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
        
        if len(runs) < 3:
            log_error(f"Insufficient runs: expected 3, got {len(runs)}")
            return False
        
        # Validate each run
        valid_runs = 0
        for run in runs:
            run_name = run.info.run_name
            metrics = run.data.metrics
            
            log_info(f"Validating run: {run_name}")
            
            # Check required metrics
            required_metrics = ['rmse', 'r2']
            missing_metrics = [m for m in required_metrics if m not in metrics]
            
            if missing_metrics:
                log_warning(f"Run {run_name} missing metrics: {missing_metrics}")
                continue
            
            # Check metric values
            rmse = metrics['rmse']
            r2 = metrics['r2']
            
            if rmse <= 0 or r2 < 0 or r2 > 1:
                log_warning(f"Run {run_name} has invalid metrics: RMSE={rmse}, R²={r2}")
                continue
            
            # Check if model artifact exists
            try:
                model_uri = f"runs:/{run.info.run_id}/model"
                model = mlflow.sklearn.load_model(model_uri)
                log_success(f"Run {run_name} validated: RMSE={rmse:.2f}, R²={r2:.3f}")
                valid_runs += 1
            except Exception as e:
                log_warning(f"Run {run_name} model loading failed: {e}")
                continue
        
        if valid_runs >= 3:
            log_success(f"Training validation passed: {valid_runs} valid runs")
            return True
        else:
            log_error(f"Training validation failed: only {valid_runs} valid runs")
            return False
        
    except Exception as e:
        log_error(f"Training validation failed: {e}")
        return False

def validate_model_files():
    """Validate that model files exist and are accessible"""
    log_info("Validating model files...")
    
    try:
        models_dir = Path("/app/models")
        if not models_dir.exists():
            log_error("Models directory not found")
            return False
        
        # Check for model files
        model_files = list(models_dir.glob("*.pkl"))
        mlflow_models = list(models_dir.glob("*/conda.yaml"))
        
        log_info(f"Found {len(model_files)} .pkl files and {len(mlflow_models)} MLflow models")
        
        if len(model_files) == 0 and len(mlflow_models) == 0:
            log_error("No model files found")
            return False
        
        # Test loading models
        testable_models = 0
        
        # Test .pkl files
        for model_file in model_files:
            try:
                import joblib
                model = joblib.load(model_file)
                log_success(f"Model loaded from {model_file.name}: {type(model).__name__}")
                testable_models += 1
            except Exception as e:
                log_warning(f"Failed to load {model_file.name}: {e}")
        
        # Test MLflow models
        for mlflow_model in mlflow_models:
            try:
                model_dir = mlflow_model.parent
                model = mlflow.sklearn.load_model(str(model_dir))
                log_success(f"MLflow model loaded from {model_dir.name}: {type(model).__name__}")
                testable_models += 1
            except Exception as e:
                log_warning(f"Failed to load MLflow model {model_dir.name}: {e}")
        
        if testable_models > 0:
            log_success(f"Model validation passed: {testable_models} testable models")
            return True
        else:
            log_error("No models could be loaded")
            return False
        
    except Exception as e:
        log_error(f"Model validation failed: {e}")
        return False

def validate_data_quality():
    """Validate data quality and availability"""
    log_info("Validating data quality...")
    
    try:
        data_file = Path("/app/data/raw/california_housing.csv")
        if not data_file.exists():
            log_error("Data file not found")
            return False
        
        # Load and validate data
        data = pd.read_csv(data_file)
        log_info(f"Data loaded: {data.shape}")
        
        # Check required columns
        required_columns = [
            'longitude', 'latitude', 'housing_median_age', 'total_rooms',
            'total_bedrooms', 'population', 'households', 'median_income',
            'median_house_value'
        ]
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            log_error(f"Missing required columns: {missing_columns}")
            return False
        
        # Check data types
        numeric_columns = [col for col in data.columns if col != 'median_house_value']
        for col in numeric_columns:
            if not pd.api.types.is_numeric_dtype(data[col]):
                log_warning(f"Column {col} is not numeric: {data[col].dtype}")
        
        # Check for missing values
        missing_counts = data.isnull().sum()
        if missing_counts.sum() > 0:
            log_warning(f"Missing values found: {missing_counts[missing_counts > 0].to_dict()}")
        
        # Check data ranges
        if len(data) < 100:
            log_warning(f"Small dataset: only {len(data)} samples")
        
        log_success("Data validation passed")
        return True
        
    except Exception as e:
        log_error(f"Data validation failed: {e}")
        return False

def main():
    """Main validation function"""
    log_info("Starting comprehensive training validation...")
    
    validation_results = []
    
    # Run all validations
    validation_results.append(("Training Results", validate_training_results()))
    validation_results.append(("Model Files", validate_model_files()))
    validation_results.append(("Data Quality", validate_data_quality()))
    
    # Summary
    log_info("\n" + "="*50)
    log_info("VALIDATION SUMMARY")
    log_info("="*50)
    
    passed = 0
    total = len(validation_results)
    
    for name, result in validation_results:
        status = "✅ PASS" if result else "❌ FAIL"
        log_info(f"{name}: {status}")
        if result:
            passed += 1
    
    log_info(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        log_success("🎉 All validations passed! Training is production-ready.")
        return True
    else:
        log_error(f"⚠️  {total - passed} validation(s) failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 