#!/usr/bin/env python3
"""
Debug script to test API requests and diagnose image upload issues
"""

import requests
import os
import sys

def test_local_api():
    """Test the local API endpoint"""
    print("=== Testing Local API ===")
    
    url = "http://127.0.0.1:8000/predict/"
    image_path = r"d:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png"
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return False
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': ('image_class1.png', f, 'image/png')}
            response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Local API test successful!")
            return True
        else:
            print("❌ Local API test failed!")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local API. Make sure it's running:")
        print("   uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Local API test error: {str(e)}")
        return False

def test_debug_endpoint():
    """Test the debug upload endpoint to see what data is received"""
    print("\n=== Testing Debug Upload Endpoint ===")
    
    url = "https://bfgtfg14yh.execute-api.ap-southeast-2.amazonaws.com/prod/debug-upload"
    api_key = "jEseEYjAD05yKdX8VadOm3M3GN5IKfxO7PkHUeNo"
    image_path = r"d:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png"
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return False
    
    try:
        headers = {
            'x-api-key': api_key,
            'accept': 'application/json'
        }
        
        with open(image_path, 'rb') as f:
            files = {'file': ('image_class1.png', f, 'image/png')}
            response = requests.post(url, files=files, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Debug endpoint test successful!")
            return True
        else:
            print("❌ Debug endpoint test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Debug endpoint test error: {str(e)}")
        return False

def test_deployed_api():
    """Test the deployed AWS API endpoint"""
    print("\n=== Testing Deployed API ===")
    
    url = "https://bfgtfg14yh.execute-api.ap-southeast-2.amazonaws.com/prod/predict/"
    api_key = "jEseEYjAD05yKdX8VadOm3M3GN5IKfxO7PkHUeNo"
    image_path = r"d:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png"
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return False
    
    try:
        headers = {
            'x-api-key': api_key,
            'accept': 'application/json'
        }
        
        with open(image_path, 'rb') as f:
            files = {'file': ('image_class1.png', f, 'image/png')}
            response = requests.post(url, files=files, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Deployed API test successful!")
            return True
        else:
            print("❌ Deployed API test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Deployed API test error: {str(e)}")
        return False

def test_health_endpoint():
    """Test the health endpoint to check if the API is working"""
    print("\n=== Testing Health Endpoint ===")
    
    url = "https://bfgtfg14yh.execute-api.ap-southeast-2.amazonaws.com/prod/health"
    api_key = "jEseEYjAD05yKdX8VadOm3M3GN5IKfxO7PkHUeNo"
    
    try:
        headers = {
            'x-api-key': api_key,
            'accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Health endpoint working!")
            return True
        else:
            print("❌ Health endpoint failed!")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint test error: {str(e)}")
        return False

def analyze_image_file():
    """Analyze the local image file"""
    print("\n=== Analyzing Image File ===")
    
    image_path = r"d:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png"
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return False
    
    try:
        with open(image_path, 'rb') as f:
            data = f.read()
        
        print(f"File size: {len(data)} bytes")
        print(f"First 10 bytes: {data[:10]}")
        
        # Check image signatures
        is_png = data.startswith(b'\x89PNG\r\n\x1a\n')
        is_jpg = data.startswith(b'\xff\xd8\xff')
        is_gif = data.startswith(b'GIF8')
        is_bmp = data.startswith(b'BM')
        
        print(f"Image format detection - PNG: {is_png}, JPG: {is_jpg}, GIF: {is_gif}, BMP: {is_bmp}")
        
        if not (is_png or is_jpg or is_gif or is_bmp):
            print("⚠️ WARNING: File does not appear to be a standard image format")
            return False
        else:
            print("✅ Image file appears to be valid")
            return True
            
    except Exception as e:
        print(f"❌ Image analysis error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 API Debug Tool")
    print("=" * 50)
    
    # Analyze the image file first
    analyze_image_file()
    
    # Test health endpoint
    test_health_endpoint()
    
    # Test debug endpoint to see what data is received
    test_debug_endpoint()
    
    # Test deployed API
    test_deployed_api()
    
    print("\n" + "=" * 50)
    print("Debug complete!")
    print("\nNext steps:")
    print("1. If health endpoint fails, check API key and deployment")
    print("2. If image analysis fails, check the image file")  
    print("3. If debug endpoint shows good data but prediction fails, check image processing")
    print("4. If deployed API fails, redeploy with updated code:")
    print("   serverless deploy --stage prod --verbose")