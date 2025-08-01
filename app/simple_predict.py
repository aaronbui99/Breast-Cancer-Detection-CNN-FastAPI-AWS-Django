from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from PIL import Image
from app.image_utils import process_uploaded_image, validate_image_for_model
import io
import os
import logging
import traceback
from app.s3_utils import S3Handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get S3 bucket name from environment variable or use a default for development
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "breast-cancer-detection-api-dev-images")

simple_predict_route = APIRouter()

def get_s3_handler():
    """Dependency to get S3 handler instance."""
    try:
        return S3Handler(S3_BUCKET_NAME)
    except Exception as e:
        logger.error(f"Failed to initialize S3 handler: {str(e)}")
        return None  # Return None instead of raising exception

@simple_predict_route.post("/")
async def simple_predict(
    file: UploadFile = File(...),
    s3_handler: S3Handler = Depends(get_s3_handler)
):
    try:
        # Read the uploaded file
        contents = await file.read()
        logger.info(f"Received file: {file.filename}, size: {len(contents)} bytes")
        
        # Try to upload to S3 if handler is available
        if s3_handler:
            try:
                s3_result = s3_handler.upload_image(contents, file.filename)
                logger.info(f"Image uploaded to S3: {s3_result['s3_key']}")
            except Exception as s3_error:
                logger.error(f"S3 upload error: {str(s3_error)}")
                logger.error(traceback.format_exc())
                s3_result = {"s3_url": "upload_failed", "s3_key": "upload_failed", "bucket": S3_BUCKET_NAME}
        else:
            logger.warning("S3 handler not available, skipping upload")
            s3_result = {"s3_url": "s3_unavailable", "s3_key": "s3_unavailable", "bucket": S3_BUCKET_NAME}
        
        # Process the image for basic validation with multiple strategies
        image = None
        error_messages = []
        
        # Strategy 1: Direct PIL approach
        try:
            logger.info("Attempting direct PIL image processing")
            image_stream = io.BytesIO(contents)
            image = Image.open(image_stream)
            image.load()  # Force load to verify
            logger.info(f"Direct PIL success: {image.format}, {image.size}, {image.mode}")
        except Exception as e1:
            error_messages.append(f"Direct PIL failed: {str(e1)}")
            logger.warning(f"Direct PIL failed: {str(e1)}")
        
        # Strategy 2: Reset stream and try again
        if image is None:
            try:
                logger.info("Attempting PIL with stream reset")
                image_stream = io.BytesIO(contents)
                image_stream.seek(0)
                image = Image.open(image_stream)
                image.load()
                logger.info(f"Reset PIL success: {image.format}, {image.size}, {image.mode}")
            except Exception as e2:
                error_messages.append(f"Reset PIL failed: {str(e2)}")
                logger.warning(f"Reset PIL failed: {str(e2)}")
        
        # Strategy 3: Copy data and try
        if image is None:
            try:
                logger.info("Attempting PIL with data copy")
                image_data_copy = bytes(contents)
                image_stream = io.BytesIO(image_data_copy)
                image = Image.open(image_stream)
                image.load()
                logger.info(f"Copy PIL success: {image.format}, {image.size}, {image.mode}")
            except Exception as e3:
                error_messages.append(f"Copy PIL failed: {str(e3)}")
                logger.warning(f"Copy PIL failed: {str(e3)}")
        
        # Strategy 4: Try without explicit load()
        if image is None:
            try:
                logger.info("Attempting PIL without explicit load")
                image_stream = io.BytesIO(contents)
                image = Image.open(image_stream)
                # Don't call load(), just get basic info
                width, height = image.size
                logger.info(f"No-load PIL success: {image.format}, {width}x{height}, {image.mode}")
            except Exception as e4:
                error_messages.append(f"No-load PIL failed: {str(e4)}")
                logger.warning(f"No-load PIL failed: {str(e4)}")
        
        if image is None:
            # All strategies failed - log detailed error info
            logger.error("All PIL strategies failed")
            logger.error(f"File info: size={len(contents)}, filename={file.filename}")
            logger.error(f"First 20 bytes: {contents[:20]}")
            logger.error(f"All errors: {error_messages}")
            
            # Return a basic response without image processing (for debugging)
            return {
                "message": "Image processing failed - using fallback response",
                "error": "PIL image processing failed with all strategies",
                "error_details": error_messages,
                "file_info": {
                    "filename": file.filename,
                    "size": len(contents),
                    "first_bytes": contents[:20].hex() if len(contents) >= 20 else contents.hex()
                },
                "prediction": 0,  # Fallback prediction
                "probability": 0.5,  # Fallback probability
                "s3_details": s3_result
            }
        
        # If we got an image, process it normally
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            width, height = image.size
            
            return {
                "message": "Simple prediction service - PyTorch unavailable, using basic image processing",
                "prediction": 0,  # Placeholder prediction (0=Benign, 1=Malignant)
                "probability": 0.5,  # Placeholder probability
                "image_details": {
                    "filename": file.filename,
                    "width": width,
                    "height": height,
                    "format": image.format,
                    "mode": image.mode,
                    "s3_url": s3_result["s3_url"],
                    "s3_key": s3_result["s3_key"],
                    "bucket": s3_result["bucket"]
                }
            }
        except Exception as process_error:
            logger.error(f"Image processing error: {str(process_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(process_error)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in simple predict endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")