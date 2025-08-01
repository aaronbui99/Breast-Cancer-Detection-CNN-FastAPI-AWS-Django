---
description: Repository Information Overview
alwaysApply: true
---

# Breast Cancer Detection API Information

## Summary
A breast cancer detection system using a CNN model, deployed as a serverless application on AWS Lambda with FastAPI. The system processes medical images to classify them as benign or malignant.

## Structure
- **app/**: Core application code including FastAPI routes and model logic
- **models/**: Contains the trained PyTorch model (best_model.pth)
- **.serverless/**: Serverless Framework deployment artifacts
- **Root directory**: Configuration files, deployment scripts, and documentation

## Language & Runtime
**Language**: Python
**Version**: Python 3.10
**Framework**: FastAPI
**Package Manager**: pip
**Deployment**: Serverless Framework

## Dependencies
**Main Dependencies**:
- fastapi: Web framework for building APIs
- uvicorn: ASGI server for FastAPI
- torch/torchvision: Deep learning framework for model inference
- Pillow: Image processing library
- mangum: AWS Lambda adapter for ASGI applications
- boto3: AWS SDK for Python

**Development Dependencies**:
- serverless-python-requirements: Serverless plugin for Python dependencies

## Build & Installation
```bash
# Setup virtual environment
python -m venv myvenv
myvenv\Scripts\activate.bat  # Windows
source myvenv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Serverless Framework
npm install -g serverless
npm install --save-dev serverless-python-requirements

# Configure AWS credentials
python setup_aws.py
```

## Deployment
```bash
# Create PyTorch Lambda layer
python create_torch_layer.py

# Deploy to AWS
serverless deploy --stage prod --verbose
serverless deploy --stage dev --verbose
```

## Docker
**Configuration**: Docker is used for packaging Python dependencies during deployment
**Requirements**: Docker Desktop 4.43.1+ for Windows
**Usage**: Automatically used by serverless-python-requirements plugin

## Testing
**Local Testing**:
```bash
# Run local development server
uvicorn app.main:app --reload
# or
python test_local.py

# Test the API
curl -X POST "http://127.0.0.1:8000/predict/" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@image_class1.png"
```

**AWS Testing**:
```bash
# Test deployed API
curl -H "x-api-key: YOUR_API_KEY" https://your-api-endpoint.execute-api.ap-southeast-2.amazonaws.com/dev/health

# Get API key
aws apigateway get-api-keys --name-query "breast-cancer-api-key-dev" --include-values
```

## AWS Resources
**Lambda Function**: Hosts the FastAPI application
**API Gateway**: Provides HTTP endpoints with API key authentication
**S3 Bucket**: Stores uploaded images for analysis
**Lambda Layer**: Contains PyTorch dependencies