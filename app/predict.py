from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from PIL import Image
import torch
import torchvision.transforms as transforms
from app.load_model import load_cnn_model
from app.image_utils import process_uploaded_image, validate_image_for_model
import io
import os
import logging
from app.s3_utils import S3Handler
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get S3 bucket name from environment variable or use a default for development
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "breast-cancer-detection-api-dev-images")

predict_route = APIRouter()

# Load model with error handling
try:
    logger.info("Attempting to load model")
    model = load_cnn_model()
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    logger.error(traceback.format_exc())
    model = None

def get_s3_handler():
    """Dependency to get S3 handler instance."""
    try:
        return S3Handler(S3_BUCKET_NAME)
    except Exception as e:
        logger.error(f"Failed to initialize S3 handler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"S3 initialization error: {str(e)}")

@predict_route.post("/")
async def predict(
    file: UploadFile = File(...),
    s3_handler: S3Handler = Depends(get_s3_handler)
):
    try:
        # Check if model is loaded
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded. Check server logs.")
        
        # Read the uploaded file
        contents = await file.read()
        logger.info(f"Received file: {file.filename}, size: {len(contents)} bytes")
        
        try:
            # Store the original image in S3
            s3_result = s3_handler.upload_image(contents, file.filename)
            logger.info(f"Image uploaded to S3: {s3_result['s3_key']}")
        except Exception as s3_error:
            logger.error(f"S3 upload error: {str(s3_error)}")
            logger.error(traceback.format_exc())
            # Continue with prediction even if S3 upload fails
            s3_result = {"s3_url": "upload_failed", "s3_key": "upload_failed", "bucket": S3_BUCKET_NAME}
        
        # Process the image for prediction
        try:
            # Use the improved image processing utility
            image = process_uploaded_image(contents, file.filename)
            
            # Validate image for model processing
            validate_image_for_model(image, target_size=(64, 64))
            
            # Apply transforms for model input
            transform = transforms.Compose([
                transforms.Resize((64, 64)),
                transforms.ToTensor(),
            ])
            input_tensor = transform(image).unsqueeze(0)
            logger.info("Image transformed for model input")

            # Make prediction
            model.eval()
            with torch.no_grad():
                output = model(input_tensor)
                prob = torch.sigmoid(output).item()
                predicted_class = 1 if prob > 0.5 else 0
                logger.info(f"Prediction complete: class={predicted_class}, probability={prob}")
                
        except ValueError as img_error:
            logger.error(f"Image processing error: {str(img_error)}")
            raise HTTPException(status_code=400, detail=f"Invalid image: {str(img_error)}")
        except Exception as pred_error:
            logger.error(f"Prediction error: {str(pred_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Prediction error: {str(pred_error)}")

        # Return prediction results along with S3 information
        return {
            "message": "Prediction successful",
            "prediction": predicted_class,
            "probability": prob,
            "image_details": {
                "filename": file.filename,
                "s3_url": s3_result["s3_url"],
                "s3_key": s3_result["s3_key"],
                "bucket": s3_result["bucket"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in predict endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")