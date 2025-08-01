#!/bin/bash
# Deploy complete hybrid architecture (Lambda + ECS)

set -e

echo "🚀 Deploying Hybrid Architecture: Lambda API + ECS PyTorch"

# Step 1: Deploy ECS infrastructure first
echo "📦 Step 1: Deploying ECS PyTorch service..."
bash deploy-ecs.sh

# Get the load balancer URL
LB_DNS=$(aws cloudformation describe-stacks \
    --stack-name breast-cancer-pytorch-ecs-prod \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text \
    --region ap-southeast-2)

echo "🔗 ECS Load Balancer: $LB_DNS"

# Step 2: Update Lambda environment variables
echo "🔧 Step 2: Updating Lambda environment variables..."

# Update serverless.yml with ECS URL
cat > temp_env.yml << EOF
# Temporary environment configuration
ECS_PYTORCH_URL: "$LB_DNS"
USE_ECS_PYTORCH: "true"
S3_BUCKET_NAME: "\${self:custom.s3BucketName}"
EOF

# Step 3: Deploy Lambda with ECS configuration
echo "⚡ Step 3: Deploying Lambda API with ECS integration..."

# Update serverless.yml environment section
python3 << EOF
import yaml

# Read serverless.yml
with open('serverless.yml', 'r') as f:
    config = yaml.safe_load(f)

# Update environment variables
if 'provider' not in config:
    config['provider'] = {}
if 'environment' not in config['provider']:
    config['provider']['environment'] = {}

config['provider']['environment']['ECS_PYTORCH_URL'] = '$LB_DNS'
config['provider']['environment']['USE_ECS_PYTORCH'] = 'true'

# Write back
with open('serverless.yml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)

print("✅ Updated serverless.yml with ECS URL")
EOF

# Deploy Lambda
serverless deploy --stage prod --region ap-southeast-2 --verbose

# Step 4: Get final endpoints
LAMBDA_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name breast-cancer-detection-api-prod \
    --query 'Stacks[0].Outputs[?OutputKey==`ServiceEndpoint`].OutputValue' \
    --output text \
    --region ap-southeast-2)

API_KEY=$(aws cloudformation describe-stacks \
    --stack-name breast-cancer-detection-api-prod \
    --query 'Stacks[0].Outputs[?contains(OutputKey, `ApiKey`)].OutputValue' \
    --output text \
    --region ap-southeast-2)

echo ""
echo "🎉 HYBRID DEPLOYMENT COMPLETE!"
echo "================================"
echo ""
echo "🌐 Architecture Overview:"
echo "  API Gateway → Lambda (FastAPI) → ECS (PyTorch)"
echo ""
echo "📡 Endpoints:"
echo "  🔹 Lambda API: $LAMBDA_ENDPOINT"
echo "  🔹 ECS PyTorch: $LB_DNS"
echo ""
echo "🔑 API Key: $API_KEY"
echo ""
echo "🧪 Test Commands:"
echo "  # Health check (Lambda)"
echo "  curl -H \"x-api-key: $API_KEY\" $LAMBDA_ENDPOINT/health"
echo ""
echo "  # Health check (ECS directly)"
echo "  curl $LB_DNS/health"
echo ""
echo "  # Prediction via Lambda → ECS"
echo "  curl -X POST \"$LAMBDA_ENDPOINT/predict/\" \\"
echo "    -H \"x-api-key: $API_KEY\" \\"
echo "    -H \"Content-Type: multipart/form-data\" \\"
echo "    -F \"file=@image_class1.png\""
echo ""
echo "✅ Deployment successful!"