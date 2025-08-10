⚙️ Setup & Configuration
1) Train & Export Model (Google Colab)
Dataset: Kaggle IDC Histopathology Images

Train a small CNN (PyTorch), save weights:

torch.save(model.state_dict(), "model.pt")  # puts in /content by default
Download model.pt and place in your repo: models/model.pt

2) Create AWS EFS (for PyTorch libs)
Why? Lambda’s glibc is older; install PyTorch into EFS and mount it to Lambda.

Create EFS

Region: same as Lambda

One Access Point (POSIX: UID/GID 1000:1000, path /python)

Add mount targets in all subnets used by Lambda

Security Groups

EFS SG: inbound NFS (TCP/2049) from your Lambda SG

Lambda SG: outbound to EFS SG (default OK)

3) One‑Time EC2 Step (install PyTorch into EFS)
Spin a small EC2 in the same VPC/subnets as EFS, attach the same SG as Lambda (or one that can reach EFS:2049):


# On EC2
sudo yum install -y amazon-efs-utils
sudo mkdir -p /mnt/efs
sudo mount -t efs -o tls,accesspoint=<EFS_ACCESS_POINT_ID> <EFS_ID>:/ /mnt/efs

# Layout for Lambda to import
sudo mkdir -p /mnt/efs/python/lib/python3.10/site-packages

# Install CPU-only torch stack into EFS (use TMPDIR on EFS to avoid EC2 disk limits)
mkdir -p /mnt/efs/tmp
export TMPDIR=/mnt/efs/tmp

python3.10 -m pip install --upgrade pip
python3.10 -m pip install --no-cache-dir \
  torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1 \
  -f https://download.pytorch.org/whl/cpu/torch_stable.html \
  -t /mnt/efs/python/lib/python3.10/site-packages

Note: You don't have to install torchaudio if you want to. I didn't :D (Aaron Bui)

# (Optional) minimal runtime deps
python3.10 -m pip install --no-cache-dir numpy pillow \
  -t /mnt/efs/python/lib/python3.10/site-packages
Verify:


PYTHONPATH=/mnt/efs/python/lib/python3.10/site-packages python3.10 - <<'PY'
import torch, torchvision, numpy, PIL
print("torch:", torch.__version__)
print("ok")
PY
You can terminate the EC2 afterwards; EFS keeps the libs.

4) FastAPI App (local check)

python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs
5) Docker (for Lambda container)
Dockerfile (minimal example):

dockerfile

FROM public.ecr.aws/lambda/python:3.10

# App code
COPY app app
COPY models models
COPY requirements-deploy.txt .

# App deps only (NOT torch—torch is in EFS)
RUN python -m pip install --no-cache-dir -r requirements-deploy.txt

# Lambda handler
CMD ["app.main.handler"]
Build & push to ECR:


aws ecr create-repository --repository-name breast-cancer-api || true
aws ecr get-login-password | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com
docker build -t breast-cancer-api .
docker tag breast-cancer-api:latest <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/breast-cancer-api:latest
docker push <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/breast-cancer-api:latest
6) Serverless Config (Lambda + EFS + API Key)
serverless.yml (essential bits only):

yaml

service: breast-cancer-detection-api

provider:
  name: aws
  region: ap-southeast-2
  runtime: python3.10
  memorySize: 1024
  timeout: 30
  iam:
    role:
      statements:
        - Effect: Allow
          Action: ["s3:GetObject","s3:PutObject"]
          Resource: "arn:aws:s3:::${self:custom.s3Bucket}/*"
  apiGateway:
    apiKeys:
      - name: breast-cancer-api-key-${sls:stage}
    usagePlan:
      throttle:
        rateLimit: 5
        burstLimit: 10
  vpc:
    securityGroupIds:
      - sg-xxxxxxxx          # Lambda SG
    subnetIds:
      - subnet-aaaaaaa
      - subnet-bbbbbbb
      - subnet-ccccccc

custom:
  s3Bucket: ${self:service}-${sls:stage}-images

functions:
  api:
    image:
      name: breast-cancer-api
      uri: <ACCOUNT>.dkr.ecr.${self:provider.region}.amazonaws.com/breast-cancer-api:latest
    fileSystemConfig:
      localMountPath: /mnt/efs
      arn: arn:aws:elasticfilesystem:${self:provider.region}:<ACCOUNT>:access-point/<EFS_ACCESS_POINT_ID>
    events:
      - http:
          path: /{proxy+}
          method: any
          private: true

resources:
  Resources:
    ImagesBucket:
      Type: AWS::S3::Bucket
      Properties:
        BucketName: ${self:custom.s3Bucket}
Ensure the Lambda SG can reach the EFS SG on TCP/2049 and the function is in the same VPC/subnets as the EFS mount targets.

7) Environment
.env (example):


S3_BUCKET_NAME=breast-cancer-detection-api-prod-images
# If you also hit S3 directly from code
AWS_REGION=ap-southeast-2
8) Deploy

# Install Serverless
npm i -g serverless
npm i --save-dev serverless-python-requirements

# Deploy
sls deploy --stage prod
Grab API key:


aws apigateway get-api-keys --name-query "breast-cancer-api-key-prod" --include-values
9) Test

# Health
curl -H "x-api-key: <KEY>" \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/health

# Predict
curl -X POST \
  -H "x-api-key: <KEY>" \
  -F "file=@sample.png" \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/predict/
Expected JSON:

json

{
  "prediction": "benign",
  "confidence": 0.92,
  "model_version": "1.0.0",
  "processing_time": 0.87
}
10) Django Integration (very short)
Store image to S3.

Call the API with x-api-key.

Display model result in your UI.

python

import requests

resp = requests.post(
  "<APIGW_URL>/predict/",
  headers={"x-api-key": "<KEY>"},
  files={"file": open("local_image.png", "rb")}
)
print(resp.json())
Notes & Tips
Keep PyTorch in EFS, not in the container.

If you see NumPy not available, install numpy into EFS (same path).

If Lambda can’t import torch, double‑check:

PYTHONPATH at runtime includes /mnt/efs/python/lib/python3.10/site-packages (the app sets it in code before importing torch), or add:

python

import sys
sys.path.insert(0, "/mnt/efs/python/lib/python3.10/site-packages")
EC2 used only for the one‑time install (then you can terminate it).