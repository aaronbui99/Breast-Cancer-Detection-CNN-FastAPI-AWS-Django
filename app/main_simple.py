import logging
import os
import sys
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from mangum import Mangum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Breast Cancer Detection API",
    description="Simplified API for breast cancer detection, deployed on AWS Lambda",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint that provides diagnostic information."""
    logger.info("Health check called")
    
    return {
        "status": "healthy",
        "mode": "simplified",
        "environment": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "s3_bucket_name": os.environ.get("S3_BUCKET_NAME", "Not set"),
            "lambda_function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Not set"),
            "lambda_function_version": os.environ.get("AWS_LAMBDA_FUNCTION_VERSION", "Not set")
        }
    }

@app.post("/predict/")
async def simple_predict(file: UploadFile = File(...)):
    """Simple prediction endpoint."""
    try:
        contents = await file.read()
        logger.info(f"Received file: {file.filename}, size: {len(contents)} bytes")
        
        # Basic file validation
        if len(contents) == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "Empty file received"}
            )
        
        # Return a simple response
        return {
            "message": "File received successfully",
            "filename": file.filename,
            "size": len(contents),
            "prediction": "placeholder - model not loaded",
            "note": "This is a simplified response. PyTorch model not available."
        }
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing error: {str(e)}"}
        )

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Breast Cancer Detection API - Simplified Mode"}

# Create a handler for AWS Lambda
handler = Mangum(app)

# Log startup information
logger.info("Simplified main application startup complete")