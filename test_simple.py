#!/usr/bin/env python3
"""
Test the main.py locally to see if imports work
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, 'app')

try:
    # Try to import the main module
    print("Testing main.py imports...")
    
    # Simulate the import conditions
    try:
        import torch
        print("✅ PyTorch available")
    except (ImportError, OSError, Exception) as e:
        print(f"❌ PyTorch failed: {type(e).__name__}: {str(e)}")
        
        # Test fallback import
        try:
            from app.simple_predict import simple_predict_route
            print("✅ Simple prediction module imported successfully")
        except Exception as e:
            print(f"❌ Simple prediction failed: {str(e)}")
            
    print("Testing FastAPI import...")
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
    
    print("Testing PIL import...")
    from PIL import Image
    print("✅ PIL imported successfully")
    
    print("Testing Mangum import...")
    from mangum import Mangum
    print("✅ Mangum imported successfully")
    
    print("\n✅ All core dependencies available")
    
except Exception as e:
    print(f"❌ Critical error: {str(e)}")
    import traceback
    traceback.print_exc()