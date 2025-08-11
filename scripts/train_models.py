#!/usr/bin/env python3
"""
Simplified Model Training Script for MLOps
Trains 3 essential models: Linear Regression, Decision Tree, and Random Forest
"""

import os
import sys
import mlflow
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_data():
    """Load California housing data"""
    try:
        # Try to load from data directory
        data_path = "data/raw/california_housing.csv"
        if os.path.exists(data_path):
            data = pd.read_csv(data_path)
            logger.info(f"Data loaded from {data_path}: {data.shape}")
        else:
            # Create sample data if file doesn't exist
            logger.info("Data file not found, creating sample data...")
            np.random.seed(42)
            n_samples = 1000

            data = {
                "longitude": np.random.uniform(-124.5, -114.0, n_samples),
                "latitude": np.random.uniform(32.5, 42.0, n_samples),
                "housing_median_age": np.random.uniform(1.0, 52.0, n_samples),
                "total_rooms": np.random.uniform(1.0, 10000.0, n_samples),
                "total_bedrooms": np.random.uniform(0.0, 5000.0, n_samples),
                "population": np.random.uniform(1.0, 50000.0, n_samples),
                "households": np.random.uniform(1.0, 5000.0, n_samples),
                "median_income": np.random.uniform(0.1, 15.0, n_samples),
                "median_house_value": np.random.uniform(50000, 500000, n_samples),
            }
            data = pd.DataFrame(data)

            # Save the sample data
            os.makedirs("data/raw", exist_ok=True)
            data.to_csv(data_path, index=False)
            logger.info(f"Sample data created and saved to {data_path}")

        return data

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None


def prepare_data(data):
    """Prepare features and target"""
    # Feature columns
    feature_cols = [
        "longitude",
        "latitude",
        "housing_median_age",
        "total_rooms",
        "total_bedrooms",
        "population",
        "households",
        "median_income",
    ]

    X = data[feature_cols].values
    y = data["median_house_value"].values

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler


def train_models(X_train, X_test, y_train, y_test):
    """Train the 3 essential models"""
    models = {
        "LinearRegression": LinearRegression(),
        "DecisionTree": DecisionTreeRegressor(max_depth=10, random_state=42),
        "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
    }

    results = {}

    for name, model in models.items():
        logger.info(f"Training {name}...")

        # Train model
        if name == "LinearRegression":
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Cross-validation score
        cv_scores = cross_val_score(
            model, X_train, y_train, cv=5, scoring="neg_mean_squared_error"
        )
        cv_rmse = np.sqrt(-cv_scores.mean())

        results[name] = {
            "model": model,
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "cv_rmse": cv_rmse,
        }

        logger.info(f"✅ {name} trained successfully. RMSE: {rmse:.2f}, R²: {r2:.3f}")

    return results


def log_to_mlflow(results, scaler):
    """Log models and metrics to MLflow"""
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("california_housing_experiment")

    for name, result in results.items():
        with mlflow.start_run(run_name=name):
            # Log parameters
            if name == "RandomForest":
                mlflow.log_param("n_estimators", 100)
                mlflow.log_param("max_depth", 10)
            elif name == "DecisionTree":
                mlflow.log_param("max_depth", 10)

            # Log metrics
            mlflow.log_metric("rmse", result["rmse"])
            mlflow.log_metric("mae", result["mae"])
            mlflow.log_metric("r2", result["r2"])
            mlflow.log_metric("cv_rmse", result["cv_rmse"])

            # Log model
            mlflow.sklearn.log_model(result["model"], "model")

            logger.info(f"✅ {name} logged to MLflow")


def save_best_model(results, scaler):
    """Save the best model locally"""
    # Find best model by RMSE
    best_name = min(results.keys(), key=lambda x: results[x]["rmse"])
    best_model = results[best_name]["model"]
    best_rmse = results[best_name]["rmse"]

    logger.info(f"Best model: {best_name} (RMSE: {best_rmse:.2f})")

    # Save best model
    import joblib
    os.makedirs("models", exist_ok=True)

    # Save the model
    model_path = "models/best_model.pkl"
    joblib.dump(best_model, model_path)
    logger.info(f"✅ Best model saved to {model_path}")

    # Save the scaler
    scaler_path = "models/scaler.pkl"
    joblib.dump(scaler, scaler_path)
    logger.info(f"✅ Scaler saved to {scaler_path}")

    return best_name, best_rmse


def main():
    """Main training function"""
    logger.info("🚀 Starting simplified model training...")

    try:
        # Load data
        data = load_data()
        if data is None:
            logger.error("Failed to load data")
            return False

        # Prepare data
        X_train, X_test, y_train, y_test, scaler = prepare_data(data)

        # Train models
        results = train_models(X_train, X_test, y_train, y_test)

        # Log to MLflow
        log_to_mlflow(results, scaler)

        # Save best model locally
        best_name, best_rmse = save_best_model(results, scaler)

        # Print summary
        logger.info("\n" + "=" * 50)
        logger.info("TRAINING SUMMARY")
        logger.info("=" * 50)
        for name, result in results.items():
            logger.info(f"{name}: RMSE: {result['rmse']:.2f}, R²: {result['r2']:.3f}")
        logger.info(f"\n🏆 Best Model: {best_name} (RMSE: {best_rmse:.2f})")
        logger.info("=" * 50)

        logger.info("🎉 Training completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)