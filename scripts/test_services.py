#!/usr/bin/env python3
"""
Service Test Script for MLOps Container
This script tests all services to ensure they're working correctly
"""

import requests
import time
import sys
from pathlib import Path

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"[SUCCESS] {message}")

def log_warning(message):
    print(f"[WARNING] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def test_api():
    """Test the FastAPI service"""
    log_info("Testing FastAPI service...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_success(f"API health: {data['status']}")
            
            # Check if model is loaded
            if data.get('model_loaded', False):
                log_success("Model is loaded and ready")
            else:
                log_warning("Model is not loaded yet")
            
            return True
        else:
            log_error(f"API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_error(f"API test failed: {e}")
        return False

def test_prediction():
    """Test prediction endpoint"""
    log_info("Testing prediction endpoint...")
    
    try:
        test_data = {
            "longitude": -118.25,
            "latitude": 34.05,
            "housing_median_age": 35.0,
            "total_rooms": 1500.0,
            "total_bedrooms": 200.0,
            "population": 500.0,
            "households": 150.0,
            "median_income": 7.5
        }
        
        response = requests.post(
            "http://localhost:8001/predict",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_success(f"Prediction successful: ${data.get('prediction', 'N/A'):,.2f}")
            return True
        else:
            log_warning(f"Prediction failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        log_error(f"Prediction test failed: {e}")
        return False

def test_mlflow():
    """Test MLflow service"""
    log_info("Testing MLflow service...")
    
    try:
        response = requests.get("http://localhost:5002", timeout=10)
        if response.status_code == 200:
            log_success("MLflow UI is accessible")
            return True
        else:
            log_error(f"MLflow test failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_error(f"MLflow test failed: {e}")
        return False

def test_prometheus():
    """Test Prometheus service"""
    log_info("Testing Prometheus service...")
    
    try:
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                log_success("Prometheus is accessible")
                
                # Check targets
                targets = data.get('data', {}).get('activeTargets', [])
                log_info(f"Found {len(targets)} active targets")
                
                for target in targets:
                    job = target.get('labels', {}).get('job', 'unknown')
                    health = target.get('health', 'unknown')
                    log_info(f"  - {job}: {health}")
                
                return True
            else:
                log_error("Prometheus returned error status")
                return False
        else:
            log_error(f"Prometheus test failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_error(f"Prometheus test failed: {e}")
        return False

def test_grafana():
    """Test Grafana service"""
    log_info("Testing Grafana service...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            log_success("Grafana is accessible")
            return True
        else:
            log_error(f"Grafana test failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_error(f"Grafana test failed: {e}")
        return False

def test_metrics():
    """Test metrics endpoint"""
    log_info("Testing metrics endpoint...")
    
    try:
        response = requests.get("http://localhost:8001/metrics", timeout=10)
        if response.status_code == 200:
            metrics = response.text
            if "http_requests_total" in metrics:
                log_success("Metrics endpoint is working")
                return True
            else:
                log_warning("Metrics endpoint returned but no expected metrics found")
                return False
        else:
            log_error(f"Metrics test failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_error(f"Metrics test failed: {e}")
        return False

def main():
    """Main test function"""
    log_info("Starting service tests...")
    
    # Wait a bit for services to be ready
    time.sleep(5)
    
    tests = [
        ("FastAPI Health", test_api),
        ("Prediction Endpoint", test_prediction),
        ("MLflow UI", test_mlflow),
        ("Prometheus", test_prometheus),
        ("Grafana", test_grafana),
        ("Metrics Endpoint", test_metrics)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            log_error(f"{test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    log_info("Service Test Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        print(f"  {icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        log_success("All services are working correctly!")
        return 0
    else:
        log_warning(f"{total - passed} service(s) have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 