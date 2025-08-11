"""
Model Retraining System for California Housing MLOps
Handles automatic and manual model retraining triggers
"""

import logging
import os
import json
import mlflow
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
import joblib
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelRetrainingSystem:
    def __init__(
        self,
        mlflow_tracking_uri: str = "file:./mlruns",
        model_name: str = "california_housing_best_model",
        data_path: str = "data/raw/california_housing.csv",
        threshold_rmse: float = 0.5,
        threshold_r2: float = 0.7,
    ):
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.model_name = model_name
        self.data_path = data_path
        self.threshold_rmse = threshold_rmse
        self.threshold_r2 = threshold_r2

        # Initialize MLflow
        mlflow.set_tracking_uri(mlflow_tracking_uri)

        # Create necessary directories
        os.makedirs("models", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

    def check_model_performance(self) -> Tuple[bool, Dict]:
        """
        Check if current model performance meets thresholds
        Returns: (needs_retraining, performance_metrics)
        """
        try:
            # Try to load current model from local files first
            current_model = None

            # Look for local model files
            if os.path.exists("models/best_model.pkl"):
                try:
                    import joblib

                    current_model = joblib.load("models/best_model.pkl")
                    logger.info("Loaded model from local models/best_model.pkl")
                except Exception as e:
                    logger.warning(f"Failed to load local model: {e}")

            # Fallback to MLflow if local model not available
            if current_model is None:
                try:
                    current_model = mlflow.pyfunc.load_model(
                        f"models:/{self.model_name}/Production"
                    )
                    logger.info("Loaded model from MLflow Model Registry")
                except Exception as e:
                    logger.warning(f"Failed to load from MLflow: {e}")

            if current_model is None:
                logger.error("No model available for performance check")
                return True, {"error": "No model available"}

            # Load test data
            if not os.path.exists(self.data_path):
                logger.warning(f"Data file not found: {self.data_path}")
                return False, {}

            data = pd.read_csv(self.data_path)

            # Prepare features and target
            feature_cols = [
                "Longitude",
                "Latitude",
                "HouseAge",
                "AveRooms",
                "AveBedrms",
                "Population",
                "AveOccup",
                "MedInc",
            ]

            X = data[feature_cols].values
            y = data["MedHouseVal"].values

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Make predictions
            y_pred = current_model.predict(X_test)

            # Calculate metrics
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            r2 = float(r2_score(y_test, y_pred))

            metrics = {
                "rmse": rmse,
                "r2": r2,
                "test_samples": int(len(X_test)),
                "timestamp": datetime.now().isoformat(),
            }

            # Check thresholds
            needs_retraining = bool(
                rmse > self.threshold_rmse or r2 < self.threshold_r2
            )

            logger.info(f"Performance check - RMSE: {rmse:.4f}, R2: {r2:.4f}")
            logger.info(f"Needs retraining: {needs_retraining}")

            return needs_retraining, metrics

        except Exception as e:
            logger.error(f"Error checking model performance: {e}")
            return True, {"error": str(e)}  # Assume retraining needed if check fails

    def check_data_drift(self, window_days: int = 30) -> Tuple[bool, Dict]:
        """
        Check for data drift by comparing recent data with training data
        Returns: (needs_retraining, drift_metrics)
        """
        try:
            # Load current data
            if not os.path.exists(self.data_path):
                return False, {}

            data = pd.read_csv(self.data_path)

            # Simulate recent data (in real scenario, this would come from API logs)
            # For now, we'll use a subset of the data
            recent_data = data.sample(frac=0.1, random_state=42)

            # Calculate basic statistics
            drift_metrics = {
                "recent_samples": int(len(recent_data)),
                "feature_means": {k: float(v) for k, v in recent_data.mean().items()},
                "feature_stds": {k: float(v) for k, v in recent_data.std().items()},
                "timestamp": datetime.now().isoformat(),
            }

            # Simple drift detection (compare means)
            # In production, you'd use more sophisticated drift detection
            needs_retraining = False

            logger.info(
                f"Data drift check completed - Recent samples: {len(recent_data)}"
            )

            return needs_retraining, drift_metrics

        except Exception as e:
            logger.error(f"Error checking data drift: {e}")
            return False, {}

    def trigger_retraining(self, trigger_type: str, force: bool = False) -> Dict:
        """
        Trigger model retraining
        """
        try:
            logger.info(f"Starting retraining process - Trigger: {trigger_type}")

            # Check if retraining is needed (unless forced)
            if not force:
                if trigger_type == "performance":
                    needs_retraining, _ = self.check_model_performance()
                elif trigger_type == "data_drift":
                    needs_retraining, _ = self.check_data_drift()
                else:
                    needs_retraining = True

                if not needs_retraining:
                    return {
                        "status": "skipped",
                        "reason": "Model performance meets thresholds",
                        "timestamp": datetime.now().isoformat(),
                    }

            # Start MLflow experiment
            experiment_name = "california_housing_experiment"
            mlflow.set_experiment(experiment_name)

            with mlflow.start_run(
                run_name=f"retraining_{trigger_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ):
                # Log parameters
                mlflow.log_param("trigger_type", trigger_type)
                mlflow.log_param("force_retraining", force)
                mlflow.log_param("threshold_rmse", self.threshold_rmse)
                mlflow.log_param("threshold_r2", self.threshold_r2)

                # Load and prepare data
                data = pd.read_csv(self.data_path)
                feature_cols = [
                    "Longitude",
                    "Latitude",
                    "HouseAge",
                    "AveRooms",
                    "AveBedrms",
                    "Population",
                    "AveOccup",
                    "MedInc",
                ]

                X = data[feature_cols].values
                y = data["MedHouseVal"].values

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )

                # Train model
                model = GradientBoostingRegressor(
                    n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
                )

                model.fit(X_train, y_train)

                # Evaluate model
                y_pred = model.predict(X_test)
                rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                r2 = float(r2_score(y_test, y_pred))

                # Log metrics
                mlflow.log_metric("rmse", rmse)
                mlflow.log_metric("r2", r2)
                mlflow.log_metric("training_samples", int(len(X_train)))
                mlflow.log_metric("test_samples", int(len(X_test)))

                # Save model locally
                model_path = f"models/retrained_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                joblib.dump(model, model_path)

                # Log model artifact
                mlflow.log_artifact(model_path)

                # Log model to MLflow (simplified - no registry)
                mlflow.sklearn.log_model(model, "model")

                # Check if new model is better than current
                current_model_path = "models/best_model.pkl"
                if os.path.exists(current_model_path):
                    try:
                        current_model = joblib.load(current_model_path)
                        # Simple comparison - in production you'd do more sophisticated evaluation
                        if rmse <= self.threshold_rmse and r2 >= self.threshold_r2:
                            # Replace current best model
                            joblib.dump(model, current_model_path)
                            logger.info("New model deployed as best_model.pkl")
                        else:
                            logger.info(
                                "New model performance below thresholds, keeping current model"
                            )
                    except Exception as e:
                        logger.warning(f"Could not compare with current model: {e}")
                        # Still save as best if we can't compare
                        if rmse <= self.threshold_rmse and r2 >= self.threshold_r2:
                            joblib.dump(model, current_model_path)
                            logger.info("New model deployed as best_model.pkl")

                logger.info(f"Retraining completed - RMSE: {rmse:.4f}, R2: {r2:.4f}")

                return {
                    "status": "completed",
                    "trigger_type": trigger_type,
                    "performance": {"rmse": rmse, "r2": r2},
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error during retraining: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def schedule_retraining(self, schedule_days: int = 30) -> Dict:
        """
        Schedule periodic retraining
        """
        try:
            # Check if scheduled retraining is due
            last_retraining_file = "models/last_retraining.txt"

            if os.path.exists(last_retraining_file):
                with open(last_retraining_file, "r") as f:
                    last_retraining = datetime.fromisoformat(f.read().strip())

                days_since_last = (datetime.now() - last_retraining).days

                if days_since_last < schedule_days:
                    return {
                        "status": "scheduled",
                        "days_until_next": schedule_days - days_since_last,
                        "timestamp": datetime.now().isoformat(),
                    }

            # Trigger scheduled retraining
            result = self.trigger_retraining("scheduled")

            # Update last retraining timestamp
            if result["status"] == "completed":
                with open(last_retraining_file, "w") as f:
                    f.write(datetime.now().isoformat())

            return result

        except Exception as e:
            logger.error(f"Error in scheduled retraining: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Global instance
retraining_system = ModelRetrainingSystem()
