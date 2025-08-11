#!/usr/bin/env python3
"""
Verification Script for MLOps Container
This script verifies that all services are working and creates sample data if needed
"""

import requests
import time
import os
from pathlib import Path

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"[SUCCESS] {message}")

def log_warning(message):
    print(f"[WARNING] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def check_api():
    """Check if API is working"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_success(f"API is healthy: {data['status']}")
            return True
        else:
            log_error(f"API health check failed: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"API check failed: {e}")
        return False

def check_mlflow():
    """Check if MLflow is working and has runs"""
    try:
        response = requests.get("http://localhost:5002", timeout=10)
        if response.status_code == 200:
            log_success("MLflow UI is accessible")
            
            # Check if we have MLflow runs
            mlruns_dir = Path("/app/mlruns")
            if mlruns_dir.exists() and any(mlruns_dir.iterdir()):
                log_success("MLflow has data")
                return True
            else:
                log_warning("MLflow has no runs")
                return False
        else:
            log_error(f"MLflow check failed: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"MLflow check failed: {e}")
        return False

def check_prometheus():
    """Check if Prometheus is working"""
    try:
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                targets = data.get('data', {}).get('activeTargets', [])
                log_success(f"Prometheus is working with {len(targets)} targets")
                return True
            else:
                log_error("Prometheus returned error status")
                return False
        else:
            log_error(f"Prometheus check failed: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Prometheus check failed: {e}")
        return False

def check_grafana():
    """Check if Grafana is working"""
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            log_success("Grafana is accessible")
            return True
        else:
            log_error(f"Grafana check failed: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Grafana check failed: {e}")
        return False

def create_sample_prediction():
    """Create a sample prediction to generate metrics"""
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
            log_success(f"Sample prediction created: ${data.get('prediction', 'N/A'):,.2f}")
            return True
        else:
            log_warning(f"Sample prediction failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_warning(f"Sample prediction failed: {e}")
        return False

def generate_metrics():
    """Generate some metrics for Prometheus and Grafana"""
    log_info("Generating metrics...")
    
    # Make multiple API calls to generate metrics
    for i in range(5):
        try:
            requests.get("http://localhost:8001/health", timeout=5)
            requests.get("http://localhost:8001/metrics", timeout=5)
            time.sleep(1)
        except:
            pass
    
    log_success("Metrics generated")

def main():
    """Main verification function"""
    log_info("Starting MLOps setup verification...")
    
    # Wait for services to be ready
    time.sleep(10)
    
    checks = [
        ("API", check_api),
        ("MLflow", check_mlflow),
        ("Prometheus", check_prometheus),
        ("Grafana", check_grafana)
    ]
    
    results = []
    for service_name, check_func in checks:
        try:
            result = check_func()
            results.append((service_name, result))
        except Exception as e:
            log_error(f"{service_name} check crashed: {e}")
            results.append((service_name, False))
    
    # Summary
    print("\n" + "="*50)
    log_info("Verification Summary:")
    
    passed = 0
    total = len(results)
    
    for service_name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        print(f"  {icon} {service_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} services working")
    
    if passed == total:
        log_success("All services are working correctly!")
        
        # Generate some metrics
        generate_metrics()
        
        # Try to create a sample prediction
        create_sample_prediction()
        
        log_info("MLOps setup is ready!")
        return 0
    else:
        log_warning(f"{total - passed} service(s) have issues")
        return 1

if __name__ == "__main__":
    exit(main()) 