#!/usr/bin/env python3
"""
Test the deployed API
"""
import requests
import json

# API configuration
API_URL = "https://bujold0o4j.execute-api.ap-southeast-2.amazonaws.com/prod"
API_KEY = "PAxZi3u4y59B4pjiuYih6kY2cC5Dgw98ZOQLAHri"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def test_health():
    """Test health endpoint"""
    print("🩺 Testing health endpoint...")
    
    try:
        response = requests.get(f"{API_URL}/health", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful!")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_prediction():
    """Test prediction endpoint"""
    print("\n🔮 Testing prediction endpoint...")
    
    image_path = "image_class1.png"
    
    try:
        # Check if image exists
        import os
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return False
        
        # Prepare file upload
        with open(image_path, 'rb') as f:
            files = {'file': f}
            headers_upload = {"x-api-key": API_KEY}  # Remove Content-Type for multipart
            
            response = requests.post(f"{API_URL}/predict/", 
                                   headers=headers_upload, 
                                   files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Prediction successful!")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return False

def test_debug_upload():
    """Test debug upload endpoint"""
    print("\n🐞 Testing debug upload endpoint...")
    
    image_path = "image_class1.png"
    
    try:
        import os
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return False
        
        with open(image_path, 'rb') as f:
            files = {'file': f}
            headers_upload = {"x-api-key": API_KEY}
            
            response = requests.post(f"{API_URL}/debug-upload", 
                                   headers=headers_upload, 
                                   files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Debug upload successful!")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Debug upload failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Debug upload error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Breast Cancer Detection API")
    print("=" * 50)
    
    # Test endpoints
    health_ok = test_health()
    debug_ok = test_debug_upload()
    prediction_ok = test_prediction()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ Health: {'PASS' if health_ok else 'FAIL'}")
    print(f"🐞 Debug Upload: {'PASS' if debug_ok else 'FAIL'}")
    print(f"🔮 Prediction: {'PASS' if prediction_ok else 'FAIL'}")
    
    if all([health_ok, debug_ok, prediction_ok]):
        print("\n🎉 All tests passed! Your API is working perfectly!")
    else:
        print("\n⚠️ Some tests failed. Check the logs above for details.")