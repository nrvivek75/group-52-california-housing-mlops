#!/usr/bin/env python3
"""
Test script for simplified training
"""

import os
import sys

def test_training():
    """Test the simplified training script"""
    print("🧪 Testing simplified training...")
    
    try:
        # Check if we're in the right directory
        if not os.path.exists("scripts/train_models.py"):
            print("❌ train_models.py not found!")
            return False
        
        # Import and test the training functions
        sys.path.append("scripts")
        from train_models import load_data, prepare_data, train_models
        
        print("✅ Training functions imported successfully")
        
        # Test data loading
        print("📊 Testing data loading...")
        data = load_data()
        if data is None:
            print("❌ Data loading failed!")
            return False
        
        print(f"✅ Data loaded: {data.shape}")
        
        # Test data preparation
        print("🔧 Testing data preparation...")
        X_train, X_test, y_train, y_test, scaler = prepare_data(data)
        print(f"✅ Data prepared: Train {X_train.shape}, Test {X_test.shape}")
        
        # Test model training
        print("🤖 Testing model training...")
        results = train_models(X_train, X_test, y_train, y_test)
        
        if len(results) == 3:
            print("✅ All 3 models trained successfully!")
            for name, result in results.items():
                print(f"   {name}: RMSE {result['rmse']:.2f}, R² {result['r2']:.3f}")
        else:
            print(f"❌ Expected 3 models, got {len(results)}")
            return False
        
        print("🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_training()
    if not success:
        sys.exit(1) 