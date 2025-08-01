#!/usr/bin/env python3

from PIL import Image
import io
import requests

def test_local_image():
    """Test the local image file"""
    try:
        img_path = r'd:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png'
        img = Image.open(img_path)
        print(f"Local image test successful:")
        print(f"  Format: {img.format}")
        print(f"  Size: {img.size}")
        print(f"  Mode: {img.mode}")
        
        # Test reading as bytes and reopening (simulating the API flow)
        with open(img_path, 'rb') as f:
            image_bytes = f.read()
        
        print(f"  File size in bytes: {len(image_bytes)}")
        
        # Test PIL opening from bytes
        img_from_bytes = Image.open(io.BytesIO(image_bytes))
        print(f"  Opening from BytesIO successful")
        print(f"  Size from BytesIO: {img_from_bytes.size}")
        
        # Test conversion to RGB
        img_rgb = img_from_bytes.convert("RGB")
        print(f"  RGB conversion successful: {img_rgb.size}")
        
        return True
        
    except Exception as e:
        print(f"Local image test failed: {str(e)}")
        return False

def test_api_multipart():
    """Test creating multipart data like curl does"""
    try:
        img_path = r'd:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png'
        
        # Read file as bytes
        with open(img_path, 'rb') as f:
            image_bytes = f.read()
        
        # Test the exact same flow as in the API
        print("\nTesting API-like processing:")
        print(f"File size: {len(image_bytes)} bytes")
        
        # Simulate what happens in the API
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        print(f"API simulation successful: {image.size}")
        
        return True
        
    except Exception as e:
        print(f"API simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Image Debug Test ===")
    test_local_image()
    test_api_multipart()