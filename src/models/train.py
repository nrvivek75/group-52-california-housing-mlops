import numpy as np
import pandas as pd
import mlflow
import logging
from pathlib import Path
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns

from .base_model import BaseModel

from ..utils.config import load_config
from ..utils.mlflow_utils import MLflowTracker
from .linear_regression import (
    LinearRegressionModel,
    RidgeRegressionModel,
    LassoRegressionModel,
)
from .random_forest import RandomForestModel


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTrainer:
    def __init__(self, config_path: str = "configs/config.yaml"):
        self.config = load_config(config_path)
        self.mlflow_tracker = MLflowTracker("california_housing_experiment")
        self.models = {}
        self.results = []

    def load_data(self):
        """Load preprocessed data"""
        processed_path = Path(self.config["data"]["processed_data_path"])

        self.X_train = np.load(processed_path / "X_train.npy")
        self.X_test = np.load(processed_path / "X_test.npy")
        self.y_train = np.load(processed_path / "y_train.npy")
        self.y_test = np.load(processed_path / "y_test.npy")

        # Load feature names
        feature_names_df = pd.read_csv(processed_path / "feature_names.csv")
        self.feature_names = feature_names_df["features"].tolist()

        logger.info(
            f"Data loaded - Train: {self.X_train.shape}, Test: {self.X_test.shape}"
        )

    def define_models(self) -> List[BaseModel]:
        """Define models to train"""
        models = [
            # Linear Models
            LinearRegressionModel(model_type="linear"),
            RidgeRegressionModel(alpha=1.0),
            RidgeRegressionModel(alpha=10.0),
            LassoRegressionModel(alpha=0.1),
            LassoRegressionModel(alpha=1.0),
            # Tree-based Models
            RandomForestModel(
                n_estimators=50, max_depth=10, min_samples_split=5, random_state=42
            ),
            RandomForestModel(
                n_estimators=100, max_depth=15, min_samples_split=2, random_state=42
            ),
            RandomForestModel(
                n_estimators=200, max_depth=20, min_samples_split=2, random_state=42
            ),
        ]

        return models

    def train_model(self, model: BaseModel) -> Dict[str, Any]:
        """Train a single model and track with MLflow"""
        with self.mlflow_tracker.start_run(run_name=f"{model.name}_experiment"):
            try:
                # Log model parameters
                self.mlflow_tracker.log_params(model.params)
                self.mlflow_tracker.log_params({"model_type": model.name})

                # Train model
                model.train(self.X_train, self.y_train)

                # Evaluate on test set
                test_metrics = model.evaluate(self.X_test, self.y_test)

                # Cross-validation metrics
                cv_metrics = model.cross_validate(self.X_train, self.y_train, cv=5)

                # Combine all metrics
                all_metrics = {**test_metrics, **cv_metrics}

                # Log metrics
                self.mlflow_tracker.log_metrics(all_metrics)

                # Log model
                self.mlflow_tracker.log_model(model.model, "model")

                # Feature importance (if available)
                feature_importance = model.get_feature_importance()
                if feature_importance is not None:
                    self.plot_feature_importance(feature_importance, model.name)

                # Save model locally
                model_path = f"models/{model.name}_model.pkl"
                model.save_model(model_path)

                # Store results
                result = {
                    "model_name": model.name,
                    "model": model,
                    "metrics": all_metrics,
                    "run_id": mlflow.active_run().info.run_id,
                }

                logger.info(
                    f"{model.name} - RMSE: {test_metrics['rmse']:.4f}, "
                    f"R2: {test_metrics['r2_score']:.4f}"
                )

                return result

            except Exception as e:
                logger.error(f"Error training {model.name}: {str(e)}")
                return None

    def plot_feature_importance(self, importance: np.ndarray, model_name: str):
        """Plot and save feature importance"""
        if len(importance) != len(self.feature_names):
            logger.warning(f"Feature importance length mismatch for {model_name}")
            return

        # Create feature importance dataframe
        feature_imp_df = pd.DataFrame(
            {"feature": self.feature_names, "importance": importance}
        ).sort_values("importance", ascending=False)

        # Plot
        plt.figure(figsize=(10, 8))
        sns.barplot(data=feature_imp_df.head(15), x="importance", y="feature")
        plt.title(f"Top 15 Feature Importance - {model_name}")
        plt.xlabel("Importance")
        plt.tight_layout()

        # Save plot
        plot_path = f"plots/{model_name}_feature_importance.png"
        Path("plots").mkdir(exist_ok=True)
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

        # Log plot as artifact
        mlflow.log_artifact(plot_path)

    def train_all_models(self):
        """Train all models"""
        models = self.define_models()

        logger.info(f"Starting training of {len(models)} models...")

        for model in models:
            result = self.train_model(model)
            if result:
                self.results.append(result)
                self.models[model.name] = result

        logger.info(
            f"Training completed. {len(self.results)} models trained successfully."
        )

    def get_best_model(self, metric: str = "rmse", ascending: bool = True):
        """Get best model based on specified metric"""
        if not self.results:
            logger.error("No models trained yet!")
            return None

        # Sort results by metric
        sorted_results = sorted(
            self.results, key=lambda x: x["metrics"][metric], reverse=not ascending
        )

        best_result = sorted_results[0]
        logger.info(
            f"Best model: {best_result['model_name']} "
            f"with {metric}: {best_result['metrics'][metric]:.4f}"
        )

        return best_result

    def compare_models(self):
        """Compare all trained models"""
        if not self.results:
            logger.error("No models trained yet!")
            return None

        # Create comparison dataframe
        comparison_data = []
        for result in self.results:
            model_data = {
                "Model": result["model_name"],
                "RMSE": result["metrics"]["rmse"],
                "MAE": result["metrics"]["mae"],
                "R2_Score": result["metrics"]["r2_score"],
                "CV_RMSE_Mean": result["metrics"]["cv_rmse_mean"],
                "CV_R2_Mean": result["metrics"]["cv_r2_mean"],
            }
            comparison_data.append(model_data)

        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.sort_values("RMSE")

        # Save comparison
        comparison_df.to_csv("models/model_comparison.csv", index=False)

        logger.info("\nModel Comparison (sorted by RMSE):")
        logger.info(comparison_df.to_string(index=False))

        return comparison_df

    def register_best_model(self, model_name: str = "california_housing_best_model"):
        """Register best model in MLflow Model Registry"""
        best_result = self.get_best_model()
        if not best_result:
            return None

        # Get model URI
        run_id = best_result["run_id"]
        model_uri = f"runs:/{run_id}/model"

        # Register model
        model_version = self.mlflow_tracker.register_model(model_uri, model_name)

        if model_version:
            logger.info(
                f"Best model registered: {model_name}, Version: {model_version.version}"
            )

            # Add model description
            self.mlflow_tracker.client.update_model_version(
                name=model_name,
                version=model_version.version,
                description=f"Best {best_result['model_name']} model with RMSE: {best_result['metrics']['rmse']:.4f}",
            )

        return model_version


def main():
    """Main training function"""
    # Initialize trainer
    trainer = ModelTrainer()

    # Load data
    trainer.load_data()

    # Train all models
    trainer.train_all_models()

    # Compare models
    comparison_df = trainer.compare_models()

    # Register best model
    trainer.register_best_model()

    # Print summary
    print("\n" + "=" * 50)
    print("TRAINING SUMMARY")
    print("=" * 50)
    print(f"Total models trained: {len(trainer.results)}")

    best_model = trainer.get_best_model()
    if best_model:
        print(f"Best model: {best_model['model_name']}")
        print(f"Best RMSE: {best_model['metrics']['rmse']:.4f}")
        print(f"Best R2 Score: {best_model['metrics']['r2_score']:.4f}")

    print("\nMLflow UI: Run 'mlflow ui' to view experiments")
    print("=" * 50)


if __name__ == "__main__":
    main()
