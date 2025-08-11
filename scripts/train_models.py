#!/usr/bin/env python3
"""
Model Training Script for California Housing
Creates and logs models to MLflow
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def load_data():
    """Load California housing data"""
    try:
        data_file = "data/raw/california_housing.csv"
        
        if not os.path.exists(data_file):
            logger.warning(f"Data file {data_file} not found, creating sample data...")
            create_sample_data()
        
        df = pd.read_csv(data_file)
        logger.info(f"Data loaded: {df.shape}")
        
        # Ensure we have the expected columns
        expected_cols = [
            'longitude', 'latitude', 'housing_median_age', 'total_rooms',
            'total_bedrooms', 'population', 'households', 'median_income', 'median_house_value'
        ]
        
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns: {missing_cols}")
            return None
        
        logger.info(f"Columns mapped: {list(df.columns)}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

def create_sample_data():
    """Create sample California housing data"""
    try:
        # Generate realistic California housing data
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
        
        # Ensure data directory exists
        os.makedirs("data/raw", exist_ok=True)
        
        # Save data
        df.to_csv("data/raw/california_housing.csv", index=False)
        logger.info(f"Sample data created with {n_samples} records")
        
        return df
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return None

def prepare_data(df):
    """Prepare data for training"""
    try:
        # Feature columns
        feature_cols = [
            'longitude', 'latitude', 'housing_median_age', 'total_rooms',
            'total_bedrooms', 'population', 'households', 'median_income'
        ]
        
        # Target column
        target_col = 'median_house_value'
        
        # Prepare features and target
        X = df[feature_cols].values
        y = df[target_col].values
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        logger.info(f"Training set: {X_train.shape}")
        logger.info(f"Test set: {X_test.shape}")
        
        return X_train_scaled, X_test_scaled, y_train, y_test, scaler
        
    except Exception as e:
        logger.error(f"Error preparing data: {e}")
        return None, None, None, None, None

def train_models(X_train, X_test, y_train, y_test, scaler):
    """Train multiple models and log to MLflow"""
    try:
        import mlflow
        import mlflow.sklearn
        from sklearn.linear_model import LinearRegression, Ridge, Lasso
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.tree import DecisionTreeRegressor
        from sklearn.metrics import mean_squared_error, r2_score
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri("file:./mlruns")
        
        # Create experiment
        experiment_name = "california_housing_experiment"
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
                logger.info(f"Created experiment: {experiment_name}")
            else:
                experiment_id = experiment.experiment_id
                logger.info(f"Using existing experiment: {experiment_name}")
        except Exception as e:
            logger.warning(f"Error with experiment: {e}")
            experiment_id = 0
        
        # Define models
        models = [
            ("Linear Regression", LinearRegression()),
            ("Decision Tree", DecisionTreeRegressor(random_state=42, max_depth=10)),
            ("Random Forest", RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10))
        ]
        
        trained_models = []
        
        # Train and log each model
        for name, model in models:
            try:
                logger.info(f"Training {name}...")
                
                # Train model
                model.fit(X_train, y_train)
                
                # Make predictions
                y_train_pred = model.predict(X_train)
                y_test_pred = model.predict(X_test)
                
                # Calculate metrics
                train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
                test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
                train_r2 = r2_score(y_train, y_train_pred)
                test_r2 = r2_score(y_test, y_test_pred)
                
                # Log to MLflow
                with mlflow.start_run(experiment_id=experiment_id, run_name=name):
                    # Log parameters
                    mlflow.log_param("model_type", name)
                    mlflow.log_param("random_state", 42)
                    
                    # Log metrics
                    mlflow.log_metric("train_rmse", train_rmse)
                    mlflow.log_metric("test_rmse", test_rmse)
                    mlflow.log_metric("train_r2", train_r2)
                    mlflow.log_metric("test_r2", test_r2)
                    mlflow.log_metric("rmse", test_rmse)  # Primary metric for model selection
                    mlflow.log_metric("r2_score", test_r2)
                    
                    # Log model
                    mlflow.sklearn.log_model(model, "model")
                    
                    # Log scaler
                    mlflow.sklearn.log_model(scaler, "scaler")
                
                logger.info(f"✅ {name} trained and logged (Test RMSE: {test_rmse:.2f})")
                trained_models.append((name, model, test_rmse))
                
            except Exception as e:
                logger.error(f"❌ Error training {name}: {e}")
                continue
        
        # Save best model locally
        if trained_models:
            best_model_info = min(trained_models, key=lambda x: x[2])
            best_name, best_model, best_rmse = best_model_info
            
            try:
                import joblib
                os.makedirs("models", exist_ok=True)
                joblib.dump(best_model, "models/best_model.pkl")
                logger.info(f"✅ Best model saved locally: {best_name} (RMSE: {best_rmse:.2f})")
            except Exception as e:
                logger.warning(f"Could not save best model locally: {e}")
        
        return len(trained_models) > 0
        
    except Exception as e:
        logger.error(f"Error in train_models: {e}")
        return False

def main():
    """Main training function"""
    logger.info("Starting model training...")
    
    try:
        # Load data
        df = load_data()
        if df is None:
            logger.error("Failed to load data")
            return False
        
        # Prepare data
        X_train, X_test, y_train, y_test, scaler = prepare_data(df)
        if X_train is None:
            logger.error("Failed to prepare data")
            return False
        
        # Train models
        success = train_models(X_train, X_test, y_train, y_test, scaler)
        
        if success:
            logger.info("✅ Model training completed successfully!")
            return True
        else:
            logger.error("❌ Model training failed")
            return False
            
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)