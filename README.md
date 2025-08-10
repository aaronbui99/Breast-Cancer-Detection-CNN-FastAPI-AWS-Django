# Breast Cancer Detection API

A comprehensive breast cancer detection system using a Convolutional Neural Network (CNN) deployed as a serverless application on AWS Lambda with FastAPI. The system processes medical histopathology images to classify them as benign or malignant.

## 🏗️ Architecture

- **Machine Learning**: CNN model trained on Kaggle IDC Histopathology Images
- **Backend**: FastAPI with Python 3.10
- **Deployment**: AWS Lambda with Container Images
- **Storage**: AWS EFS for PyTorch libraries, S3 for image storage
- **API Gateway**: RESTful API with API key authentication
- **Integration**: Django-compatible API endpoints

## 🚀 Features

- Real-time breast cancer classification
- RESTful API with comprehensive documentation
- Serverless architecture for cost efficiency
- Secure API key authentication
- S3 integration for image storage
- Django framework integration support

## 📋 Prerequisites

- Python 3.10+
- Docker Desktop 4.43.1+
- AWS CLI configured
- Node.js and npm (for Serverless Framework)
- AWS account with appropriate permissions

## 🛠️ Setup & Installation

### 1. Model Training & Export

Train your CNN model using Google Colab with the Kaggle IDC Histopathology Images dataset:

```python
# Save your trained model
torch.save(model.state_dict(), "model.pt")
```

Download and place the model file in: `models/best_model.pth`

### 2. Local Development Environment

```bash
# Create and activate virtual environment
python -m venv myvenv
# Windows
myvenv\Scripts\activate.bat
# macOS/Linux
source myvenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run local development server
uvicorn app.main:app --reload
```

Access the API documentation at: `http://127.0.0.1:8000/docs`

### 3. AWS Infrastructure Setup

#### Create AWS EFS (for PyTorch Libraries)

1. Create EFS in the same region as your Lambda
2. Create Access Point with POSIX settings (UID/GID 1000:1000, path `/python`)
3. Configure mount targets in all Lambda subnets
4. Set up security groups:
   - EFS SG: Allow inbound NFS (TCP/2049) from Lambda SG
   - Lambda SG: Allow outbound to EFS SG

#### Install PyTorch into EFS (One-time EC2 Setup)

```bash
# Launch EC2 in same VPC/subnets as EFS
sudo yum install -y amazon-efs-utils
sudo mkdir -p /mnt/efs
sudo mount -t efs -o tls,accesspoint=<EFS_ACCESS_POINT_ID> <EFS_ID>:/ /mnt/efs

# Create Python library structure
sudo mkdir -p /mnt/efs/python/lib/python3.10/site-packages

# Install PyTorch CPU version
mkdir -p /mnt/efs/tmp
export TMPDIR=/mnt/efs/tmp

python3.10 -m pip install --upgrade pip
python3.10 -m pip install --no-cache-dir \
  torch==1.13.1 torchvision==0.14.1 \
  -f https://download.pytorch.org/whl/cpu/torch_stable.html \
  -t /mnt/efs/python/lib/python3.10/site-packages

# Install additional dependencies
python3.10 -m pip install --no-cache-dir numpy pillow \
  -t /mnt/efs/python/lib/python3.10/site-packages
```

Verify installation:
```bash
PYTHONPATH=/mnt/efs/python/lib/python3.10/site-packages python3.10 -c "import torch, torchvision, numpy, PIL; print('All libraries installed successfully')"
```

### 4. Container Deployment

#### Build and Push Docker Image

```bash
# Create ECR repository
aws ecr create-repository --repository-name breast-cancer-api || true

# Login to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com

# Build and push image
docker build -t breast-cancer-api .
docker tag breast-cancer-api:latest <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/breast-cancer-api:latest
docker push <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/breast-cancer-api:latest
```

### 5. Serverless Deployment

#### Install Serverless Framework

```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements
```

#### Configure Environment

Create `.env` file:
```
S3_BUCKET_NAME=breast-cancer-detection-api-prod-images
AWS_REGION=ap-southeast-2
```

#### Deploy to AWS

```bash
# Deploy to production
serverless deploy --stage prod --verbose

# Deploy to development
serverless deploy --stage dev --verbose
```

#### Get API Key

```bash
aws apigateway get-api-keys --name-query "breast-cancer-api-key-prod" --include-values
```

## 🔧 Usage

### API Endpoints

#### Health Check
```bash
curl -H "x-api-key: <YOUR_API_KEY>" \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/health
```

#### Predict Breast Cancer
```bash
curl -X POST \
  -H "x-api-key: <YOUR_API_KEY>" \
  -F "file=@sample.png" \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/predict/
```

### Expected Response

```json
{
  "prediction": "benign",
  "confidence": 0.92,
  "model_version": "1.0.0",
  "processing_time": 0.87
}
```

### Django Integration

```python
import requests

def predict_breast_cancer(image_path, api_key, api_url):
    response = requests.post(
        f"{api_url}/predict/",
        headers={"x-api-key": api_key},
        files={"file": open(image_path, "rb")}
    )
    return response.json()

# Usage
result = predict_breast_cancer("image.png", "your-api-key", "https://your-api-endpoint.com")
print(result)
```

## 🧪 Testing

### Local Testing

```bash
# Run local server
python test_local.py

# Test API endpoints
curl -X POST "http://127.0.0.1:8000/predict/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image_class1.png"
```

### Production Testing

```bash
# Test health endpoint
python test_api.py

# Test prediction endpoint
python test_dev_api.py
```

## 📁 Project Structure

```
├── app/                          # Core application code
│   ├── main.py                   # FastAPI application
│   ├── predict.py                # Prediction logic
│   ├── model.py                  # CNN model definition
│   ├── image_utils.py            # Image processing utilities
│   └── s3_utils.py              # AWS S3 integration
├── models/                       # Trained model files
│   └── best_model.pth           # PyTorch model weights
├── .serverless/                  # Serverless deployment artifacts
├── requirements.txt              # Python dependencies
├── requirements-deploy.txt       # Deployment-specific dependencies
├── serverless.yml               # Serverless configuration
├── Dockerfile                   # Container configuration
└── README.md                    # Project documentation
```

## ⚠️ Troubleshooting

### Common Issues

1. **NumPy Import Error**: Install numpy into EFS at the same path as PyTorch
2. **PyTorch Import Error**: Verify PYTHONPATH includes EFS mount path
3. **Lambda Timeout**: Increase timeout in serverless.yml (current: 30s)
4. **Memory Issues**: Increase memorySize in serverless.yml (current: 1024MB)

### Debug Commands

```bash
# Check ECS logs
python check_ecs_logs.py

# Check ECS status
python check_ecs_status.py

# Debug API requests
python debug_api_request.py
```

## 🔒 Security

- API key authentication for all endpoints
- VPC isolation for Lambda functions
- Encrypted S3 storage for uploaded images
- IAM roles with minimal required permissions

## 📊 Performance

- **Cold Start**: ~2-3 seconds (with EFS mount)
- **Warm Invocation**: ~0.5-1 second
- **Memory Usage**: ~800MB (with PyTorch loaded)
- **Concurrent Requests**: 10 burst limit, 5 requests/second

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Bui Thanh Huy (Aaron Bui)**
- Email: aaronhuy2509@gmail.com
- LinkedIn: [Huy Bui Thanh](https://www.linkedin.com/in/huy-bui-thanh-372a56194/)

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Serverless Framework](https://www.serverless.com/framework/docs/)
- [PyTorch Documentation](https://pytorch.org/docs/)