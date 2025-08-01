"""
Simple debug endpoint to test image uploads without complex processing
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
import io
import logging
import sys
import os

logger = logging.getLogger(__name__)

debug_router = APIRouter()

@debug_router.post("/debug-simple")
async def debug_simple_upload(file: UploadFile = File(...)):
    """Simple debug endpoint to test image upload"""
    try:
        logger.info(f"=== DEBUG SIMPLE UPLOAD ===")
        logger.info(f"Filename: {file.filename}")
        logger.info(f"Content Type: {file.content_type}")
        
        # Read file contents
        contents = await file.read()
        logger.info(f"File size: {len(contents)} bytes")
        
        if len(contents) == 0:
            return {"error": "Empty file", "success": False}
            
        # Check first few bytes
        first_bytes = contents[:10]
        logger.info(f"First 10 bytes: {first_bytes}")
        
        # Try to create BytesIO
        try:
            image_stream = io.BytesIO(contents)
            logger.info("BytesIO stream created successfully")
            
            # Try PIL opening
            try:
                image = Image.open(image_stream)
                logger.info(f"PIL opened image: format={image.format}, size={image.size}, mode={image.mode}")
                
                return {
                    "success": True,
                    "filename": file.filename,
                    "size": len(contents),
                    "format": image.format,
                    "image_size": image.size,
                    "mode": image.mode,
                    "first_bytes": first_bytes.hex()
                }
                
            except Exception as pil_error:
                logger.error(f"PIL error: {pil_error}")
                return {
                    "error": f"PIL error: {str(pil_error)}",
                    "success": False,
                    "size": len(contents),
                    "first_bytes": first_bytes.hex()
                }
                
        except Exception as stream_error:
            logger.error(f"BytesIO error: {stream_error}")
            return {
                "error": f"BytesIO error: {str(stream_error)}",
                "success": False,
                "size": len(contents)
            }
            
    except Exception as e:
        logger.error(f"General error: {e}")
        return {"error": f"General error: {str(e)}", "success": False}


@debug_router.get("/debug-torch")
async def debug_torch_import():
    """Debug endpoint to test PyTorch imports and layer availability"""
    try:
        result = {
            "python_version": sys.version,
            "python_path": sys.path,
            "environment_vars": dict(os.environ),
            "torch_import": None,
            "torchvision_import": None,
            "torch_version": None,
            "torchvision_version": None,
            "torch_location": None,
            "available_modules": [],
        }
        
        # Check available modules in sys.modules
        torch_related = [name for name in sys.modules.keys() if 'torch' in name.lower()]
        result["available_modules"] = sorted(torch_related)
        
        # Try importing torch
        try:
            import torch
            result["torch_import"] = "SUCCESS"
            result["torch_version"] = torch.__version__
            result["torch_location"] = torch.__file__
            logger.info(f"PyTorch imported successfully: {torch.__version__}")
        except ImportError as e:
            result["torch_import"] = f"FAILED: {str(e)}"
            logger.error(f"PyTorch import failed: {e}")
        except Exception as e:
            result["torch_import"] = f"ERROR: {str(e)}"
            logger.error(f"PyTorch import error: {e}")
        
        # Try importing torchvision
        try:
            import torchvision
            result["torchvision_import"] = "SUCCESS"
            result["torchvision_version"] = torchvision.__version__
            logger.info(f"TorchVision imported successfully: {torchvision.__version__}")
        except ImportError as e:
            result["torchvision_import"] = f"FAILED: {str(e)}"
            logger.error(f"TorchVision import failed: {e}")
        except Exception as e:
            result["torchvision_import"] = f"ERROR: {str(e)}"
            logger.error(f"TorchVision import error: {e}")
        
        # Check if torch modules are available in different paths
        lambda_paths = [
            "/opt/python",
            "/opt/python/lib/python3.10/site-packages",
            "/var/runtime",
            "/var/task"
        ]
        
        result["path_checks"] = {}
        for path in lambda_paths:
            if os.path.exists(path):
                result["path_checks"][path] = os.listdir(path)[:10]  # First 10 items
            else:
                result["path_checks"][path] = "PATH_NOT_EXISTS"
        
        return result
        
    except Exception as e:
        logger.error(f"Debug torch error: {e}")
        return {"error": f"Debug error: {str(e)}", "success": False}