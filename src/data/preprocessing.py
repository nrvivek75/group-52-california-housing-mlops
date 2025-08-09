import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from pathlib import Path
import joblib

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='median')
        self.feature_names = None
        
    def load_raw_data(self, file_path: str) -> pd.DataFrame:
        """Load raw data from CSV file"""
        return pd.read_csv(file_path)
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the dataset"""
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle outliers using IQR method
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        numeric_columns = numeric_columns.drop('MedHouseVal')  # Don't remove outliers from target
        
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        
        return df
    
    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create new features"""
        # Create new features
        df['rooms_per_household'] = df['AveRooms'] / df['AveOccup']
        df['bedrooms_per_room'] = df['AveBedrms'] / df['AveRooms']
        df['population_per_household'] = df['Population'] / df['HouseAge']
        
        # Log transform skewed features
        skewed_features = ['Population', 'AveOccup']
        for feature in skewed_features:
            df[f'{feature}_log'] = np.log1p(df[feature])
        
        return df
    
    def split_features_target(self, df: pd.DataFrame):
        """Split features and target variable"""
        X = df.drop('MedHouseVal', axis=1)
        y = df['MedHouseVal']
        return X, y
    
    def preprocess_features(self, X_train, X_test=None, fit=True):
        """Preprocess features with scaling and imputation"""
        if fit:
            # Fit imputer and scaler on training data
            X_train_imputed = self.imputer.fit_transform(X_train)
            X_train_scaled = self.scaler.fit_transform(X_train_imputed)
            self.feature_names = X_train.columns.tolist()
            
            if X_test is not None:
                X_test_imputed = self.imputer.transform(X_test)
                X_test_scaled = self.scaler.transform(X_test_imputed)
                return X_train_scaled, X_test_scaled
            
            return X_train_scaled
        else:
            # Transform only
            X_imputed = self.imputer.transform(X_train)
            X_scaled = self.scaler.transform(X_imputed)
            return X_scaled
    
    def save_preprocessor(self, filepath: str):
        """Save the fitted preprocessor"""
        joblib.dump({
            'scaler': self.scaler,
            'imputer': self.imputer,
            'feature_names': self.feature_names
        }, filepath)
    
    def load_preprocessor(self, filepath: str):
        """Load a fitted preprocessor"""
        components = joblib.load(filepath)
        self.scaler = components['scaler']
        self.imputer = components['imputer']
        self.feature_names = components['feature_names']

def preprocess_data():
    """Main preprocessing pipeline"""
    # Initialize preprocessor
    preprocessor = DataPreprocessor()
    
    # Load raw data
    raw_data_path = "data/raw/california_housing.csv"
    df = preprocessor.load_raw_data(raw_data_path)
    
    print(f"Original dataset shape: {df.shape}")
    
    # Clean data
    df_clean = preprocessor.clean_data(df)
    print(f"After cleaning: {df_clean.shape}")
    
    # Feature engineering
    df_engineered = preprocessor.feature_engineering(df_clean)
    print(f"After feature engineering: {df_engineered.shape}")
    
    # Split features and target
    X, y = preprocessor.split_features_target(df_engineered)
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=pd.qcut(y, q=5, duplicates='drop')
    )
    
    print(f"Training set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")
    
    # Preprocess features
    X_train_processed, X_test_processed = preprocessor.preprocess_features(
        X_train, X_test, fit=True
    )
    
    # Create processed data directory
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save processed data
    np.save(processed_dir / "X_train.npy", X_train_processed)
    np.save(processed_dir / "X_test.npy", X_test_processed)
    np.save(processed_dir / "y_train.npy", y_train.values)
    np.save(processed_dir / "y_test.npy", y_test.values)
    
    # Save feature names
    pd.Series(preprocessor.feature_names).to_csv(
        processed_dir / "feature_names.csv", index=False, header=['features']
    )
    
    # Save preprocessor
    preprocessor.save_preprocessor(processed_dir / "preprocessor.pkl")
    
    print("Data preprocessing completed successfully!")
    
    return X_train_processed, X_test_processed, y_train, y_test

if __name__ == "__main__":
    preprocess_data()