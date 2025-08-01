#!/usr/bin/env python3
"""
Test the corrected file upload approach
"""
import requests
import os

def test_corrected_upload():
    """Test file upload with proper multipart handling"""
    url = "https://bfgtfg14yh.execute-api.ap-southeast-2.amazonaws.com/prod/predict/"
    api_key = "jEseEYjAD05yKdX8VadOm3M3GN5IKfxO7PkHUeNo"
    image_path = r"D:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png"
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return False
    
    try:
        headers = {
            'x-api-key': api_key,
            'accept': 'application/json'
            # Note: We DO NOT set Content-Type manually for multipart uploads
        }
        
        # This is the correct way - let requests handle Content-Type automatically
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/png')}
            response = requests.post(url, files=files, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ File upload test successful!")
            result = response.json()
            
            # Check if we got a proper prediction result
            if "prediction" in result and "probability" in result:
                prediction = result["prediction"]
                probability = result["probability"]
                print(f"🎯 Prediction: {prediction} ({'Malignant' if prediction == 1 else 'Benign'})")
                print(f"📊 Probability: {probability:.3f}")
                
                if "image_details" in result:
                    print(f"📁 S3 URL: {result['image_details'].get('s3_url', 'N/A')}")
                
            return True
        else:
            print("❌ File upload test failed!")
            return False
            
    except Exception as e:
        print(f"❌ File upload test error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Corrected File Upload")
    print("=" * 50)
    test_corrected_upload()