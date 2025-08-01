import logging
import os
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import basic dependencies first
try:
    from fastapi import FastAPI, UploadFile, File, Request
    from fastapi.responses import JSONResponse
    from PIL import Image
    import io
    from mangum import Mangum
    
    # Log successful imports
    logger.info("Successfully imported basic dependencies")
    
    # Check prediction method preference
    use_ecs_pytorch = os.getenv('USE_ECS_PYTORCH', 'true').lower() == 'true'
    
    if use_ecs_pytorch:
        # Use ECS-based PyTorch prediction (recommended)
        try:
            from app.ecs_predict import ecs_predict_route, ecs_health_check
            prediction_method = "ecs_pytorch"
            logger.info("Using ECS-based PyTorch prediction service")
        except (ImportError, Exception) as ecs_error:
            logger.warning(f"ECS prediction not available: {ecs_error}")
            use_ecs_pytorch = False
    
    if not use_ecs_pytorch:
        # Try to import PyTorch dependencies for local processing
        try:
            import torch
            import torchvision
            from app.predict import predict_route
            prediction_method = "local_pytorch"
            logger.info("Using local PyTorch prediction model")
        except (ImportError, OSError, Exception) as torch_error:
            logger.warning(f"PyTorch not available: {torch_error}")
            # Fall back to simple prediction without PyTorch
            try:
                from app.simple_predict import simple_predict_route
                prediction_method = "simple"
                logger.info("Using simplified prediction model (no PyTorch)")
            except (ImportError, Exception) as simple_error:
                logger.error(f"Failed to import simple prediction: {simple_error}")
                raise
    
    # Initialize FastAPI app
    app = FastAPI(
        title="Breast Cancer Detection API",
        description="API for breast cancer detection using CNN model, deployed on AWS Lambda",
        version="1.0.0"
    )
    
    # Include the appropriate prediction router
    if prediction_method == "ecs_pytorch":
        # Add ECS-based prediction routes
        @app.post("/predict/")
        async def predict_endpoint(file: UploadFile = File(...)):
            return await ecs_predict_route(file)
    elif prediction_method == "local_pytorch":
        app.include_router(predict_route)
    else:  # simple prediction
        app.include_router(simple_predict_route, prefix="/predict")
    
    # Include debug router for troubleshooting
    try:
        from app.debug_endpoint import debug_router
        app.include_router(debug_router)
        logger.info("Debug router included successfully")
    except Exception as debug_import_error:
        logger.warning(f"Could not include debug router: {debug_import_error}")
    
    # Add a health check endpoint
    @app.get("/health")
    async def health_check():
        # Log environment information
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Directory contents: {os.listdir('.')}")
        
        if os.path.exists("models"):
            logger.info(f"Models directory contents: {os.listdir('models')}")
        else:
            logger.info("Models directory not found")
        
        # Check environment variables
        s3_bucket = os.environ.get("S3_BUCKET_NAME", "Not set")
        logger.info(f"S3_BUCKET_NAME: {s3_bucket}")
        
        # Check PyTorch availability
        torch_version = torch.__version__ if 'torch' in sys.modules else "Not available"
        torchvision_version = torchvision.__version__ if 'torchvision' in sys.modules else "Not available"
        
        return {
            "status": "healthy",
            "prediction_method": prediction_method,
            "environment": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "s3_bucket_name": s3_bucket,
                "torch_version": torch_version,
                "torchvision_version": torchvision_version,
                "use_ecs_pytorch": os.getenv('USE_ECS_PYTORCH', 'false')
            }
        }
    
    # Add a debug endpoint to analyze uploaded files
    @app.post("/debug-upload")
    async def debug_upload(file: UploadFile = File(...)):
        try:
            # Read the uploaded file
            contents = await file.read()
            
            # Analyze the received data
            analysis = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(contents),
                "first_20_bytes": contents[:20].hex() if len(contents) >= 20 else contents.hex(),
                "last_20_bytes": contents[-20:].hex() if len(contents) >= 20 else contents.hex()
            }
            
            # Check file signatures
            signatures = {
                'PNG': contents.startswith(b'\x89PNG\r\n\x1a\n'),
                'JPEG': contents.startswith(b'\xff\xd8\xff'),
                'GIF87a': contents.startswith(b'GIF87a'),
                'GIF89a': contents.startswith(b'GIF89a'), 
                'BMP': contents.startswith(b'BM'),
                'WEBP': contents.startswith(b'RIFF')
            }
            
            analysis["detected_formats"] = {k: v for k, v in signatures.items() if v}
            
            # Try to create a BytesIO stream and test PIL
            try:
                image_stream = io.BytesIO(contents)
                analysis["bytesio_created"] = True
                analysis["bytesio_size"] = len(image_stream.getvalue())
                
                # Test PIL opening
                try:
                    test_image = Image.open(image_stream)
                    analysis["pil_success"] = True
                    analysis["pil_format"] = test_image.format
                    analysis["pil_mode"] = test_image.mode
                    analysis["pil_size"] = test_image.size
                except Exception as pil_error:
                    analysis["pil_success"] = False
                    analysis["pil_error"] = str(pil_error)
                    
            except Exception as stream_error:
                analysis["bytesio_created"] = False
                analysis["bytesio_error"] = str(stream_error)
            
            logger.info(f"Debug upload analysis: {analysis}")
            return {"status": "debug_complete", "analysis": analysis}
            
        except Exception as e:
            logger.error(f"Debug upload error: {str(e)}")
            return {"status": "debug_error", "error": str(e)}
    
    # Add global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error",
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    
    # Create a handler for AWS Lambda
    handler = Mangum(app)
    
    # Log startup information
    logger.info("Main application startup complete")

except ImportError as e:
    # If dependencies are missing, use the fallback app
    logger.error(f"Missing dependency: {str(e)}")
    logger.error("Falling back to minimal API")
    
    try:
        # Import the fallback module
        from app.fallback import fallback_handler as handler
        logger.info("Fallback handler initialized")
    except Exception as fallback_error:
        logger.critical(f"Failed to initialize fallback handler: {str(fallback_error)}")
        logger.critical(traceback.format_exc())
        
        # As a last resort, create a minimal handler
        from mangum import Mangum
        from fastapi import FastAPI
        
        minimal_app = FastAPI()
        
        @minimal_app.get("/{path:path}")
        @minimal_app.post("/{path:path}")
        async def minimal_handler(path: str):
            return {
                "message": "Service Unavailable",
                "detail": f"Critical dependency error: {str(e)}",
                "path": path
            }
        
        handler = Mangum(minimal_app)
        logger.info("Minimal emergency handler initialized")

except Exception as e:
    # Catch any other initialization errors
    logger.critical(f"Unexpected error during initialization: {str(e)}")
    logger.critical(traceback.format_exc())
    
    # Create an absolute minimal handler as last resort
    from mangum import Mangum
    from fastapi import FastAPI
    
    emergency_app = FastAPI()
    
    @emergency_app.get("/{path:path}")
    @emergency_app.post("/{path:path}")
    async def emergency_handler(path: str):
        return {
            "message": "Service Unavailable",
            "detail": "Critical system error",
            "path": path
        }
    
    handler = Mangum(emergency_app)
    logger.info("Emergency handler initialized due to critical error")

