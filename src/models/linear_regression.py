from sklearn.linear_model import LinearRegression, Ridge, Lasso
from .base_model import BaseModel

class LinearRegressionModel(BaseModel):
    def __init__(self, model_type='linear', **kwargs):
        self.model_type = model_type
        super().__init__(name=f"LinearRegression_{model_type}", **kwargs)
    
    def build_model(self):
        """Build linear regression model"""
        if self.model_type == 'linear':
            self.model = LinearRegression(**self.params)
        elif self.model_type == 'ridge':
            self.model = Ridge(**self.params)
        elif self.model_type == 'lasso':
            self.model = Lasso(**self.params)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

class RidgeRegressionModel(BaseModel):
    def __init__(self, alpha=1.0, **kwargs):
        super().__init__(name="RidgeRegression", alpha=alpha, **kwargs)
    
    def build_model(self):
        """Build Ridge regression model"""
        self.model = Ridge(**self.params)

class LassoRegressionModel(BaseModel):
    def __init__(self, alpha=1.0, **kwargs):
        super().__init__(name="LassoRegression", alpha=alpha, **kwargs)
    
    def build_model(self):
        """Build Lasso regression model"""
        self.model = Lasso(**self.params)