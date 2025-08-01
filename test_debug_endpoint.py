"""
Quick test for the debug endpoint
"""

import requests
import os

def test_debug_endpoint():
    """Test the simple debug endpoint"""
    url = "https://bfgtfg14yh.execute-api.ap-southeast-2.amazonaws.com/prod/debug-simple"
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

if __name__ == "__main__":
    print("🔧 Testing Debug Endpoint")
    print("=" * 40)
    test_debug_endpoint()