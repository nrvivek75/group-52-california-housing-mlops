#!/usr/bin/env python3
"""
Test Setup Script for California Housing MLOps Project
Verifies that all components are working correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required packages can be imported"""
    print("🔍 Testing package imports...")
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False
    
    try:
        import sklearn
        print("✅ scikit-learn imported successfully")
    except ImportError as e:
        print(f"❌ scikit-learn import failed: {e}")
        return False
    
    try:
        import mlflow
        print("✅ mlflow imported successfully")
    except ImportError as e:
        print(f"❌ mlflow import failed: {e}")
        return False
    
    try:
        import fastapi
        print("✅ fastapi imported successfully")
    except ImportError as e:
        print(f"❌ fastapi import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ uvicorn import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    try:
        sys.path.append(str(Path(__file__).parent.parent / "src"))
        from utils.config import load_config
        
        config = load_config("configs/config.yaml")
        print("✅ Configuration loaded successfully")
        print(f"   MLflow experiment: {config['mlflow']['experiment_name']}")
        print(f"   Data path: {config['data']['raw_data_path']}")
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_directories():
    """Test that required directories exist or can be created"""
    print("\n🔍 Testing directories...")
    
    required_dirs = [
        "logs",
        "models", 
        "mlruns",
        "data/raw",
        "data/processed"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            except Exception as e:
                print(f"❌ Failed to create directory {dir_path}: {e}")
                return False
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    return True

def test_api_import():
    """Test that the API can be imported"""
    print("\n🔍 Testing API import...")
    
    try:
        sys.path.append(str(Path(__file__).parent.parent / "src"))
        from api import app
        
        print("✅ FastAPI app imported successfully")
        print(f"   App title: {app.title}")
        print(f"   App version: {app.version}")
        return True
    except Exception as e:
        print(f"❌ API import failed: {e}")
        return False

def test_docker():
    """Test Docker availability"""
    print("\n🔍 Testing Docker...")
    
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is available")
            print(f"   Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker command failed")
            return False
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def test_mlflow_setup():
    """Test MLflow setup"""
    print("\n🔍 Testing MLflow setup...")
    
    try:
        import mlflow
        
        # Test setting tracking URI
        mlflow.set_tracking_uri("file:./mlruns")
        print("✅ MLflow tracking URI set successfully")
        
        # Test setting experiment
        mlflow.set_experiment("test_experiment")
        print("✅ MLflow experiment set successfully")
        
        return True
    except Exception as e:
        print(f"❌ MLflow setup failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 California Housing MLOps - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Directories", test_directories),
        ("API Import", test_api_import),
        ("Docker", test_docker),
        ("MLflow Setup", test_mlflow_setup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"⚠️ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\n🚀 Next steps:")
        print("   1. Download California Housing dataset to data/raw/")
        print("   2. Run: python scripts/train_models.py")
        print("   3. Run: python src/api.py")
        print("   4. Or use: make start")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 