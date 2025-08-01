import logging
import os
import sys
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mangum import Mangum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize a minimal FastAPI app for fallback
fallback_app = FastAPI(
    title="Breast Cancer Detection API (Fallback Mode)",
    description="Fallback API when dependencies are missing",
    version="1.0.0"
)

@fallback_app.get("/health")
async def health_check():
    """Health check endpoint that provides diagnostic information."""
    return {
        "status": "degraded",
        "message": "Running in fallback mode due to missing dependencies",
        "environment": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "available_modules": list(sys.modules.keys()),
            "environment_variables": {k: v for k, v in os.environ.items() if not k.startswith("AWS_")}
        }
    }

@fallback_app.get("/{path:path}")
@fallback_app.post("/{path:path}")
async def fallback_handler(path: str):
    """Catch-all handler for all routes when in fallback mode."""
    logger.warning(f"Request received for path: {path} while in fallback mode")
    return JSONResponse(
        status_code=503,
        content={
            "message": "Service Temporarily Unavailable",
            "detail": "The service is running in fallback mode due to missing dependencies. Please contact the administrator.",
            "path": path
        }
    )

# Create a handler for AWS Lambda
fallback_handler = Mangum(fallback_app)