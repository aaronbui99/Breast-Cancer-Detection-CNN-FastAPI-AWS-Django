"""
Test the image processing locally to understand the issue
"""

from PIL import Image
import io

def test_image_processing():
    """Test image processing with the same file used in API calls"""
    image_path = r"d:\Documents\Git\Breast-Cancer-Detection-CNN-FastAPI-AWS-Django\image_class1.png"
    
    print("🧪 Local Image Processing Test")
    print("=" * 40)
    
    try:
        # Read the file
        with open(image_path, 'rb') as f:
            contents = f.read()
        
        print(f"✅ File read successfully: {len(contents)} bytes")
        print(f"First 10 bytes: {contents[:10]}")
        
        # Test BytesIO creation
        image_stream = io.BytesIO(contents)
        print("✅ BytesIO stream created")
        
        # Test PIL opening
        image = Image.open(image_stream)
        print(f"✅ PIL opened image: {image.format}, {image.size}, {image.mode}")
        
        # Test loading
        image.load()
        print("✅ Image loaded successfully")
        
        # Test RGB conversion
        if image.mode != 'RGB':
            image = image.convert('RGB')
            print(f"✅ Converted to RGB: {image.size}")
        else:
            print("✅ Already in RGB mode")
            
        # Test pixel access
        pixel = image.getpixel((0, 0))
        print(f"✅ Pixel access successful: {pixel}")
        
        print("\n🎉 All local tests passed!")
        print("The image file is valid locally - the issue is in the Lambda environment.")
        
        return True
        
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        return False

if __name__ == "__main__":
    test_image_processing()