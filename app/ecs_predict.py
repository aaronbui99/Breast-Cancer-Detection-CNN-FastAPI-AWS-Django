"""
ECS-based prediction module
Calls the ECS PyTorch inference service
"""
import os
import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

class ECSPredictionService:
    """Service to handle predictions via ECS"""
    
    def __init__(self):
        # Get ECS service URL from environment
        self.ecs_url = os.getenv('ECS_PYTORCH_URL', 'http://localhost:8080')
        self.timeout = 30  # 30 second timeout
        logger.info(f"ECS Prediction Service initialized with URL: {self.ecs_url}")
    
    async def predict(self, file: UploadFile) -> Dict[str, Any]:
        """
        Send prediction request to ECS service
        """
        try:
            # Read file content
            file_content = await file.read()
            
            # Reset file pointer for potential reuse
            file.file.seek(0)
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field('file', 
                          file_content, 
                          filename=file.filename,
                          content_type=file.content_type)
            
            # Make request to ECS service
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.ecs_url}/predict/",
                    data=data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info("ECS prediction successful")
                        return {
                            **result,
                            "processing_method": "ecs_pytorch",
                            "ecs_url": self.ecs_url
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"ECS service error {response.status}: {error_text}")
                        raise HTTPException(
                            status_code=502,
                            detail=f"ECS service error: {response.status}"
                        )
                        
        except asyncio.TimeoutError:
            logger.error("ECS service timeout")
            raise HTTPException(
                status_code=504,
                detail="ECS service timeout"
            )
        except aiohttp.ClientError as e:
            logger.error(f"ECS service connection error: {e}")
            raise HTTPException(
                status_code=502,
                detail="Cannot connect to ECS service"
            )
        except Exception as e:
            logger.error(f"ECS prediction error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"ECS prediction failed: {str(e)}"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check ECS service health
        """
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.ecs_url}/health") as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "ecs_service": "healthy",
                            "ecs_url": self.ecs_url,
                            "ecs_details": result
                        }
                    else:
                        return {
                            "ecs_service": "unhealthy",
                            "ecs_url": self.ecs_url,
                            "status_code": response.status
                        }
                        
        except Exception as e:
            logger.warning(f"ECS health check failed: {e}")
            return {
                "ecs_service": "unavailable",
                "ecs_url": self.ecs_url,
                "error": str(e)
            }

# Global instance
ecs_service = ECSPredictionService()

async def ecs_predict_route(file: UploadFile) -> Dict[str, Any]:
    """
    Route function for ECS-based prediction
    """
    return await ecs_service.predict(file)

async def ecs_health_check() -> Dict[str, Any]:
    """
    Health check for ECS service
    """
    return await ecs_service.health_check()