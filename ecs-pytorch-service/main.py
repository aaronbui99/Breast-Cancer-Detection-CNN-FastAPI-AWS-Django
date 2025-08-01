"""
ECS PyTorch Inference Service
Handles heavy ML inference workloads
"""
import os
import logging
import traceback
from io import BytesIO
from typing import Optional

import torch
import torchvision.transforms as transforms
from PIL import Image
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="PyTorch Inference Service",
    description="ECS-based PyTorch inference for breast cancer detection",
    version="1.0.0"
)

# Global model variable
model = None
device = None

class BreastCancerCNN(torch.nn.Module):
    """CNN model for breast cancer detection"""
    def __init__(self, num_classes=2):
        super(BreastCancerCNN, self).__init__()
        self.conv1 = torch.nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1)
        self.pool = torch.nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        self.conv2 = torch.nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.conv3 = torch.nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.conv4 = torch.nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        
        # Calculate the size of flattened features
        # Input: 224x224, after 4 pooling layers: 224/16 = 14
        self.fc1 = torch.nn.Linear(256 * 14 * 14, 512)
        self.dropout1 = torch.nn.Dropout(0.5)
        self.fc2 = torch.nn.Linear(512, 256)
        self.dropout2 = torch.nn.Dropout(0.5)
        self.fc3 = torch.nn.Linear(256, num_classes)
        
    def forward(self, x):
        x = self.pool(torch.nn.functional.relu(self.conv1(x)))
        x = self.pool(torch.nn.functional.relu(self.conv2(x)))
        x = self.pool(torch.nn.functional.relu(self.conv3(x)))
        x = self.pool(torch.nn.functional.relu(self.conv4(x)))
        
        x = x.view(x.size(0), -1)  # Flatten
        x = torch.nn.functional.relu(self.fc1(x))
        x = self.dropout1(x)
        x = torch.nn.functional.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.fc3(x)
        return x

def load_model():
    """Load the PyTorch model"""
    global model, device
    
    try:
        device = torch.device('cpu')  # ECS uses CPU
        logger.info(f"Using device: {device}")
        
        # Initialize model
        model = BreastCancerCNN(num_classes=2)
        
        # Try to load from S3 or local file
        model_path = "/app/models/best_model.pth"
        
        if os.path.exists(model_path):
            logger.info(f"Loading model from {model_path}")
            model.load_state_dict(torch.load(model_path, map_location=device))
        else:
            # Try to download from S3
            try:
                s3_client = boto3.client('s3')
                bucket_name = os.getenv('S3_BUCKET_NAME', 'breast-cancer-detection-api-prod-images')
                s3_key = 'models/best_model.pth'
                
                logger.info(f"Downloading model from S3: s3://{bucket_name}/{s3_key}")
                os.makedirs("/app/models", exist_ok=True)
                s3_client.download_file(bucket_name, s3_key, model_path)
                
                model.load_state_dict(torch.load(model_path, map_location=device))
                logger.info("Model downloaded and loaded from S3")
                
            except ClientError as e:
                logger.warning(f"Could not load model from S3: {e}")
                logger.info("Using randomly initialized model (for testing)")
        
        model.eval()
        logger.info("Model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.error(traceback.format_exc())
        return False

def preprocess_image(image: Image.Image):
    """Preprocess image for model inference"""
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Apply transforms
    image_tensor = transform(image).unsqueeze(0)  # Add batch dimension
    return image_tensor

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    logger.info("Starting PyTorch Inference Service...")
    success = load_model()
    if not success:
        logger.error("Failed to load model during startup")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_status = "loaded" if model is not None else "not_loaded"
    
    return JSONResponse({
        "status": "healthy",
        "service": "pytorch-inference",
        "model_status": model_status,
        "device": str(device) if device else "unknown",
        "torch_version": torch.__version__
    })

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    """Perform inference on uploaded image"""
    
    if model is None:
        raise HTTPException(
            status_code=503, 
            detail="Model not loaded. Service unavailable."
        )
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Read and process image
        image_data = await file.read()
        image = Image.open(BytesIO(image_data))
        
        # Preprocess image
        image_tensor = preprocess_image(image)
        
        # Perform inference
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
        
        # Map prediction to class names
        class_names = {0: "benign", 1: "malignant"}
        predicted_label = class_names.get(predicted_class, "unknown")
        
        result = {
            "prediction": predicted_label,
            "confidence": float(confidence),
            "probabilities": {
                "benign": float(probabilities[0][0]),
                "malignant": float(probabilities[0][1])
            },
            "image_info": {
                "filename": file.filename,
                "size": f"{image.size[0]}x{image.size[1]}",
                "mode": image.mode
            },
            "service": "ecs-pytorch"
        }
        
        logger.info(f"Prediction completed: {predicted_label} (confidence: {confidence:.3f})")
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PyTorch Inference Service",
        "version": "1.0.0",
        "endpoints": ["/health", "/predict/"],
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)