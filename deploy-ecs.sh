#!/bin/bash
# Deploy ECS PyTorch Infrastructure and Service

set -e

# Configuration
AWS_REGION="ap-southeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SERVICE_NAME="breast-cancer-pytorch"
IMAGE_TAG="latest"
ECR_REPO_NAME="$SERVICE_NAME"

echo "🚀 Deploying ECS PyTorch Infrastructure..."
echo "Account ID: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo "Service: $SERVICE_NAME"

# Step 1: Deploy ECS infrastructure
echo "📦 Step 1: Deploying ECS infrastructure..."
serverless deploy --config ecs-infrastructure.yml --stage prod --region $AWS_REGION

# Get ECR repository URI
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
echo "ECR URI: $ECR_URI"

# Step 2: Build and push Docker image
echo "🐳 Step 2: Building and pushing Docker image..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Build image
docker build --platform linux/amd64 -t $SERVICE_NAME:$IMAGE_TAG ./ecs-pytorch-service/

# Tag image
docker tag $SERVICE_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG

# Push image
docker push $ECR_URI:$IMAGE_TAG

# Step 3: Update ECS service
echo "🔄 Step 3: Updating ECS service..."
CLUSTER_NAME="${SERVICE_NAME}-cluster-prod"
SERVICE_NAME_FULL="${SERVICE_NAME}-service"

# Force new deployment to use the new image
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME_FULL \
    --force-new-deployment \
    --region $AWS_REGION

# Step 4: Get load balancer URL
echo "🌐 Step 4: Getting service endpoints..."
LB_DNS=$(aws cloudformation describe-stacks \
    --stack-name breast-cancer-pytorch-ecs-prod \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text \
    --region $AWS_REGION)

echo ""
echo "✅ ECS Deployment Complete!"
echo "🔗 Load Balancer URL: $LB_DNS"
echo "🩺 Health Check: $LB_DNS/health"
echo ""
echo "📝 Next steps:"
echo "1. Wait for ECS service to become stable (2-3 minutes)"
echo "2. Test the health endpoint: curl $LB_DNS/health"
echo "3. Update Lambda environment variable: ECS_PYTORCH_URL=$LB_DNS"
echo ""