from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score
import joblib
from pathlib import Path
from typing import Dict, Any, Tuple
import logging

class BaseModel(ABC):
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.model = None
        self.is_trained = False
        self.params = kwargs
    
    @abstractmethod
    def build_model(self):
        """Build the model with given parameters"""
        pass
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> 'BaseModel':
        """Train the model"""
        if self.model is None:
            self.build_model()
        
        logging.info(f"Training {self.name} model...")
        self.model.fit(X_train, y_train)
        self.is_trained = True
        logging.info(f"{self.name} model training completed")
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        return self.model.predict(X)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        y_pred = self.predict(X_test)
        
        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred),
            'r2_score': r2_score(y_test, y_pred),
            'mse': mean_squared_error(y_test, y_pred)
        }
        
        return metrics
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray, cv: int = 5) -> Dict[str, float]:
        """Perform cross-validation"""
        if self.model is None:
            self.build_model()
        
        # Perform cross-validation for different metrics
        rmse_scores = np.sqrt(-cross_val_score(self.model, X, y, cv=cv, scoring='neg_mean_squared_error'))
        mae_scores = -cross_val_score(self.model, X, y, cv=cv, scoring='neg_mean_absolute_error')
        r2_scores = cross_val_score(self.model, X, y, cv=cv, scoring='r2')
        
        cv_metrics = {
            'cv_rmse_mean': rmse_scores.mean(),
            'cv_rmse_std': rmse_scores.std(),
            'cv_mae_mean': mae_scores.mean(),
            'cv_mae_std': mae_scores.std(),
            'cv_r2_mean': r2_scores.mean(),
            'cv_r2_std': r2_scores.std()
        }
        
        return cv_metrics
    
    def save_model(self, filepath: str):
        """Save trained model"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, filepath)
        logging.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        self.model = joblib.load(filepath)
        self.is_trained = True
        logging.info(f"Model loaded from {filepath}")
    
    def get_feature_importance(self) -> np.ndarray:
        """Get feature importance if available"""
        if hasattr(self.model, 'feature_importances_'):
            return self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            return np.abs(self.model.coef_)
        else:
            return None