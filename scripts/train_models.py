#!/usr/bin/env python3
"""
Model Training Script for California Housing MLOps Project
Trains multiple models and registers the best one with MLflow
"""

import os
import sys
import logging
from pathlib import Path
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
import yaml

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map sklearn dataset column names to expected column names"""
    column_mapping = {
        'Longitude': 'longitude',
        'Latitude': 'latitude', 
        'HouseAge': 'housing_median_age',
        'AveRooms': 'total_rooms',
        'AveBedrms': 'total_bedrooms',
        'Population': 'population',
        'AveOccup': 'households',
        'MedInc': 'median_income',
        'MedHouseVal': 'median_house_value'
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Convert target to thousands of dollars (sklearn dataset is in 100k units)
    df['median_house_value'] = df['median_house_value'] * 100000
    
    return df

class ModelTrainer:
    """Train and evaluate multiple models for California Housing dataset"""
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        self.config = load_config(config_path)
        self.setup_mlflow()
        self.models = {}
        self.results = []
        
    def setup_mlflow(self):
        """Setup MLflow tracking"""
        mlflow.set_tracking_uri(self.config['mlflow']['tracking_uri'])
        mlflow.set_experiment(self.config['mlflow']['experiment_name'])
        logger.info(f"MLflow tracking URI: {self.config['mlflow']['tracking_uri']}")
        logger.info(f"MLflow experiment: {self.config['mlflow']['experiment_name']}")
    
    def load_data(self):
        """Load and preprocess the California Housing dataset"""
        try:
            # Load raw data
            data_path = Path(self.config['data']['raw_data_path'])
            if not data_path.exists():
                logger.error(f"Data file not found: {data_path}")
                raise FileNotFoundError(f"Data file not found: {data_path}")
            
            # Load data
            self.data = pd.read_csv(data_path)
            logger.info(f"Data loaded: {self.data.shape}")
            
            # Map column names to expected format
            self.data = map_columns(self.data)
            logger.info(f"Columns mapped: {list(self.data.columns)}")
            
            # Prepare features and target
            feature_columns = [
                'longitude', 'latitude', 'housing_median_age', 'total_rooms',
                'total_bedrooms', 'population', 'households', 'median_income'
            ]
            
            self.X = self.data[feature_columns].values
            self.y = self.data['median_house_value'].values
            
            # Split data
            test_size = self.config['data']['test_size']
            random_state = self.config['data']['random_state']
            
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                self.X, self.y, test_size=test_size, random_state=random_state
            )
            
            # Scale features
            self.scaler = StandardScaler()
            self.X_train_scaled = self.scaler.fit_transform(self.X_train)
            self.X_test_scaled = self.scaler.transform(self.X_test)
            
            logger.info(f"Training set: {self.X_train.shape}")
            logger.info(f"Test set: {self.X_test.shape}")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def define_models(self):
        """Define models to train"""
        models_config = self.config['models']
        
        self.models = {
            'Linear Regression': {
                'model': LinearRegression(),
                'params': models_config['linear_regression']['params']
            },
            'Ridge Regression': {
                'model': Ridge(),
                'params': models_config['ridge_regression']['params']
            },
            'Lasso Regression': {
                'model': Lasso(),
                'params': models_config['lasso_regression']['params']
            },
            'Random Forest': {
                'model': RandomForestRegressor(random_state=42),
                'params': models_config['random_forest']['params']
            },
            'Decision Tree': {
                'model': DecisionTreeRegressor(random_state=42),
                'params': {}
            },
            'Gradient Boosting': {
                'model': GradientBoostingRegressor(random_state=42),
                'params': {
                    'n_estimators': [50, 100],
                    'learning_rate': [0.1, 0.2],
                    'max_depth': [3, 5]
                }
            }
        }
        
        logger.info(f"Defined {len(self.models)} models for training")
    
    def train_model(self, model_name: str, model_instance, hyperparams: dict):
        """Train a single model with hyperparameter tuning"""
        logger.info(f"Training {model_name}...")
        
        with mlflow.start_run(run_name=f"{model_name}_experiment"):
            try:
                # Log model parameters
                mlflow.log_params({"model_name": model_name})
                
                # Hyperparameter tuning if parameters are provided
                best_model = model_instance
                if hyperparams:
                    from sklearn.model_selection import GridSearchCV
                    
                    grid_search = GridSearchCV(
                        model_instance, 
                        hyperparams, 
                        cv=self.config['training']['cv_folds'],
                        scoring=self.config['training']['scoring'],
                        n_jobs=-1
                    )
                    
                    grid_search.fit(self.X_train_scaled, self.y_train)
                    best_model = grid_search.best_estimator_
                    
                    # Log best parameters
                    mlflow.log_params(grid_search.best_params_)
                    logger.info(f"Best parameters for {model_name}: {grid_search.best_params_}")
                
                # Train the model
                best_model.fit(self.X_train_scaled, self.y_train)
                
                # Make predictions
                y_train_pred = best_model.predict(self.X_train_scaled)
                y_test_pred = best_model.predict(self.X_test_scaled)
                
                # Calculate metrics
                metrics = self.calculate_metrics(best_model, y_train_pred, y_test_pred)
                
                # Log metrics
                for metric_name, value in metrics.items():
                    mlflow.log_metric(metric_name, value)
                
                # Log model
                mlflow.sklearn.log_model(best_model, f"{model_name.lower().replace(' ', '_')}")
                
                # Store results
                result = {
                    'model_name': model_name,
                    'model': best_model,
                    'metrics': metrics,
                    'run_id': mlflow.active_run().info.run_id
                }
                
                self.results.append(result)
                
                logger.info(f"{model_name} training completed. RMSE: {metrics['test_rmse']:.4f}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                mlflow.log_param("error", str(e))
                return None
    
    def calculate_metrics(self, best_model, y_train_pred, y_test_pred):
        """Calculate various performance metrics"""
        metrics = {}
        
        # Training metrics
        metrics['train_rmse'] = np.sqrt(mean_squared_error(self.y_train, y_train_pred))
        metrics['train_mae'] = mean_absolute_error(self.y_train, y_train_pred)
        metrics['train_r2'] = r2_score(self.y_train, y_train_pred)
        
        # Test metrics
        metrics['test_rmse'] = np.sqrt(mean_squared_error(self.y_test, y_test_pred))
        metrics['test_mae'] = mean_absolute_error(self.y_test, y_test_pred)
        metrics['test_r2'] = r2_score(self.y_test, y_test_pred)
        
        # Cross-validation score
        cv_scores = cross_val_score(
            best_model, 
            self.X_train_scaled, 
            self.y_train, 
            cv=self.config['training']['cv_folds'],
            scoring=self.config['training']['scoring']
        )
        metrics['cv_score_mean'] = -cv_scores.mean()  # Convert back to positive
        metrics['cv_score_std'] = cv_scores.std()
        
        return metrics
    
    def train_all_models(self):
        """Train all defined models"""
        logger.info("Starting training of all models...")
        
        for model_name, model_info in self.models.items():
            try:
                result = self.train_model(
                    model_name, 
                    model_info['model'], 
                    model_info['params']
                )
                
                if result:
                    logger.info(f"✅ {model_name} trained successfully")
                else:
                    logger.warning(f"⚠️ {model_name} training failed")
                    
            except Exception as e:
                logger.error(f"❌ Error training {model_name}: {e}")
        
        logger.info(f"Training completed. {len(self.results)} models trained successfully.")
    
    def select_best_model(self, metric: str = 'test_rmse', ascending: bool = True):
        """Select the best model based on specified metric"""
        if not self.results:
            logger.error("No models trained yet")
            return None
        
        # Sort results by metric
        sorted_results = sorted(
            self.results, 
            key=lambda x: x['metrics'][metric], 
            reverse=not ascending
        )
        
        best_result = sorted_results[0]
        logger.info(f"Best model: {best_result['model_name']}")
        logger.info(f"Best {metric}: {best_result['metrics'][metric]:.4f}")
        
        return best_result
    
    def register_best_model(self, model_name: str = None):
        """Register the best model in MLflow Model Registry"""
        if not model_name:
            model_name = self.config['mlflow']['registered_model_name']
        
        best_result = self.select_best_model()
        if not best_result:
            logger.error("No best model to register")
            return None
        
        try:
            # Register model
            mlflow.sklearn.log_model(
                best_result['model'],
                "model",
                registered_model_name=model_name
            )
            
            # Transition to Production
            client = mlflow.tracking.MlflowClient()
            latest_version = client.get_latest_versions(model_name, stages=["None"])[0]
            
            client.transition_model_version_stage(
                name=model_name,
                version=latest_version.version,
                stage="Production"
            )
            
            logger.info(f"✅ Best model registered and moved to Production: {model_name}")
            
            # Save model locally for API use
            model_path = Path("models")
            model_path.mkdir(exist_ok=True)
            
            import joblib
            joblib.dump(best_result['model'], model_path / "best_model.pkl")
            joblib.dump(self.scaler, model_path / "scaler.pkl")
            
            logger.info(f"✅ Model saved locally to {model_path}")
            
            return best_result
            
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            return None
    
    def generate_report(self):
        """Generate training report"""
        if not self.results:
            logger.warning("No results to report")
            return
        
        logger.info("\n" + "="*50)
        logger.info("TRAINING REPORT")
        logger.info("="*50)
        
        # Sort by test RMSE
        sorted_results = sorted(self.results, key=lambda x: x['metrics']['test_rmse'])
        
        for i, result in enumerate(sorted_results):
            logger.info(f"\n{i+1}. {result['model_name']}")
            logger.info(f"   Test RMSE: {result['metrics']['test_rmse']:.4f}")
            logger.info(f"   Test MAE:  {result['metrics']['test_mae']:.4f}")
            logger.info(f"   Test R²:   {result['metrics']['test_r2']:.4f}")
            logger.info(f"   CV Score:  {result['metrics']['cv_score_mean']:.4f} ± {result['metrics']['cv_score_std']:.4f}")
        
        logger.info("\n" + "="*50)

def main():
    """Main training function"""
    try:
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Initialize trainer
        trainer = ModelTrainer()
        
        # Load data
        trainer.load_data()
        
        # Define models
        trainer.define_models()
        
        # Train all models
        trainer.train_all_models()
        
        # Generate report
        trainer.generate_report()
        
        # Register best model
        trainer.register_best_model()
        
        logger.info("🎉 Model training completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()