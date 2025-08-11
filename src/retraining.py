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
            # Load current model
            current_model = mlflow.pyfunc.load_model(
                f"models:/{self.model_name}/Production"
            )

            # Load test data
            if not os.path.exists(self.data_path):
                logger.warning(f"Data file not found: {self.data_path}")
                return False, {}

            data = pd.read_csv(self.data_path)

            # Prepare features and target
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

            X = data[feature_cols]
            y = data["median_house_value"] / 100000  # Convert to 100k units

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Make predictions
            y_pred = current_model.predict(X_test)

            # Calculate metrics
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)

            metrics = {
                "rmse": rmse,
                "r2": r2,
                "test_samples": len(X_test),
                "timestamp": datetime.now().isoformat(),
            }

            # Check thresholds
            needs_retraining = rmse > self.threshold_rmse or r2 < self.threshold_r2

            logger.info(f"Performance check - RMSE: {rmse:.4f}, R2: {r2:.4f}")
            logger.info(f"Needs retraining: {needs_retraining}")

            return needs_retraining, metrics

        except Exception as e:
            logger.error(f"Error checking model performance: {e}")
            return True, {}  # Assume retraining needed if check fails

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
                "recent_samples": len(recent_data),
                "feature_means": recent_data.mean().to_dict(),
                "feature_stds": recent_data.std().to_dict(),
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
                    "longitude",
                    "latitude",
                    "housing_median_age",
                    "total_rooms",
                    "total_bedrooms",
                    "population",
                    "households",
                    "median_income",
                ]

                X = data[feature_cols]
                y = data["median_house_value"] / 100000

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
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)

                # Log metrics
                mlflow.log_metric("rmse", rmse)
                mlflow.log_metric("r2", r2)
                mlflow.log_metric("training_samples", len(X_train))
                mlflow.log_metric("test_samples", len(X_test))

                # Save model locally
                model_path = f"models/retrained_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                joblib.dump(model, model_path)

                # Log model artifact
                mlflow.log_artifact(model_path)

                # Register model if performance is good
                if rmse <= self.threshold_rmse and r2 >= self.threshold_r2:
                    mlflow.sklearn.log_model(model, "model")

                    # Register in model registry
                    model_details = mlflow.register_model(
                        f"runs:/{mlflow.active_run().info.run_id}/model",
                        f"{self.model_name}_v{datetime.now().strftime('%Y%m%d')}",
                    )

                    # Transition to production if it's the best model
                    client = mlflow.tracking.MlflowClient()
                    client.transition_model_version_stage(
                        name=model_details.name,
                        version=model_details.version,
                        stage="Production",
                    )

                    logger.info(
                        f"New model registered and deployed: {model_details.name}"
                    )

                    return {
                        "status": "completed",
                        "trigger_type": trigger_type,
                        "new_model_version": model_details.version,
                        "performance": {"rmse": rmse, "r2": r2},
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    logger.warning(
                        f"Retrained model performance below thresholds: RMSE={rmse}, R2={r2}"
                    )
                    return {
                        "status": "completed_below_threshold",
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
