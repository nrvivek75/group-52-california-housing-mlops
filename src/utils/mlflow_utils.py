import mlflow
import mlflow.sklearn
import mlflow.xgboost
from mlflow.tracking import MlflowClient
import os
from typing import Dict, Any, Optional
import logging

class MLflowTracker:
    def __init__(self, experiment_name: str = "california_housing_experiment"):
        """Initialize MLflow tracking"""
        # Set tracking URI (local for demo, can be remote server in production)
        mlflow.set_tracking_uri("file:./mlruns")
        
        # Set or create experiment
        try:
            experiment_id = mlflow.create_experiment(experiment_name)
        except mlflow.exceptions.MlflowException:
            experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
        
        mlflow.set_experiment(experiment_name)
        self.experiment_name = experiment_name
        self.client = MlflowClient()
        
        logging.info(f"MLflow experiment '{experiment_name}' initialized")
    
    def start_run(self, run_name: str = None):
        """Start MLflow run"""
        return mlflow.start_run(run_name=run_name)
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters"""
        mlflow.log_params(params)
    
    def log_metrics(self, metrics: Dict[str, float]):
        """Log metrics"""
        mlflow.log_metrics(metrics)
    
    def log_model(self, model, model_name: str, **kwargs):
        """Log model based on its type"""
        if hasattr(model, 'get_booster'):  # XGBoost
            mlflow.xgboost.log_model(model, model_name, **kwargs)
        else:  # Sklearn models
            mlflow.sklearn.log_model(model, model_name, **kwargs)
    
    def log_artifacts(self, artifacts_path: str):
        """Log artifacts"""
        mlflow.log_artifacts(artifacts_path)
    
    def register_model(self, model_uri: str, model_name: str):
        """Register model in MLflow Model Registry"""
        try:
            model_version = mlflow.register_model(model_uri, model_name)
            logging.info(f"Model registered: {model_name}, Version: {model_version.version}")
            return model_version
        except Exception as e:
            logging.error(f"Failed to register model: {e}")
            return None
    
    def get_best_run(self, metric_name: str = "rmse", ascending: bool = True):
        """Get best run based on metric"""
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=[f"metrics.{metric_name} {'ASC' if ascending else 'DESC'}"]
        )
        return runs.iloc[0] if not runs.empty else None