import os
import pandas as pd
import requests
from pathlib import Path

def download_california_housing():
    """
    Download California Housing dataset from a reliable source
    Since we can't directly access Kaggle API without authentication,
    we'll use sklearn's built-in dataset which is the same data
    """
    from sklearn.datasets import fetch_california_housing
    
    # Create data directory if it doesn't exist
    raw_data_dir = Path("data/raw")
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch the dataset
    print("Downloading California Housing dataset...")
    housing = fetch_california_housing(as_frame=True)
    
    # Combine features and target
    df = housing.frame
    
    # Save to CSV
    output_path = raw_data_dir / "california_housing.csv"
    df.to_csv(output_path, index=False)
    
    print(f"Dataset saved to {output_path}")
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    return df

if __name__ == "__main__":
    download_california_housing()