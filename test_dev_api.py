#!/usr/bin/env python3
"""
Test script for dev API
"""
import requests
import json

def test_dev_api():
    # API configuration for dev
    base_url = "https://lkmy15hc52.execute-api.ap-southeast-2.amazonaws.com/dev"
    api_key = "jEseEYjAD05yKdX8VadOm3M3GN5IKfxO7PkHUeNo"
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    print("Testing DEV API...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Test health endpoint
    try:
        print("1. Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed!")
            result = response.json()
            print(f"Status: {result.get('status', 'Unknown')}")
            
            # Print environment info
            env = result.get('environment', {})
            print(f"Python Version: {env.get('python_version', 'Unknown')[:50]}...")
            print(f"PyTorch Version: {env.get('torch_version', 'Unknown')}")
            print(f"Working Directory: {env.get('working_directory', 'Unknown')}")
            
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling health endpoint: {str(e)}")
    
    print("-" * 50)
    
    # Test predict endpoint
    try:
        print("2. Testing /predict endpoint (without file)...")
        response = requests.post(f"{base_url}/predict/", headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 422:  # Expected - missing file
            print("✅ Predict endpoint is accessible (as expected, missing file parameter)")
        elif response.status_code == 200:
            print("✅ Predict endpoint accessible, got response")
        print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling predict endpoint: {str(e)}")

if __name__ == "__main__":
    test_dev_api()