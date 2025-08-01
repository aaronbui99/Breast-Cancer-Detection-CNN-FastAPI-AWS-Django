"""
Minimal prediction endpoint that bypasses PIL completely
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

logger = logging.getLogger(__name__)

minimal_router = APIRouter()

@minimal_router.post("/")
async def minimal_predict(file: UploadFile = File(...)):
    """
    Minimal prediction endpoint that bypasses PIL completely
    Returns basic file info and placeholder prediction
    """
    try:
        logger.info("=== MINIMAL PREDICT ENDPOINT ===")
        
        # Read file contents
        contents = await file.read()
        
        # Basic file validation
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        # Check file signatures
        file_signatures = {
            'PNG': contents.startswith(b'\x89PNG\r\n\x1a\n'),
            'JPEG': contents.startswith(b'\xff\xd8\xff'),
            'GIF87a': contents.startswith(b'GIF87a'),
            'GIF89a': contents.startswith(b'GIF89a'), 
            'BMP': contents.startswith(b'BM'),
            'WEBP': contents.startswith(b'RIFF')
        }
        
        detected_formats = [k for k, v in file_signatures.items() if v]
        
        if not detected_formats:
            raise HTTPException(status_code=400, detail="Unrecognized image format")
        
        # Return successful response without PIL processing
        return {
            "message": "Minimal prediction service - PIL bypassed successfully",
            "status": "success",
            "prediction": 0,  # Benign (placeholder)
            "probability": 0.45,  # Placeholder probability
            "confidence": "low",  # Since this is just a placeholder
            "file_details": {
                "filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(contents),
                "detected_formats": detected_formats,
                "first_bytes": contents[:20].hex(),
                "is_valid_image": len(detected_formats) > 0
            },
            "processing_info": {
                "method": "minimal_bypass",
                "torch_available": False,
                "pil_bypassed": True,
                "reason": "PIL processing failed in Lambda environment"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Minimal predict error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")