# Fixing AWS Lambda Layer Size Limit Issue

You're encountering the AWS Lambda layer size limit (250MB unzipped). Here are three solutions to fix this:

## Solution 1: Optimized PyTorch Layer (Quick Fix)

Use the optimized layer creation script that removes unnecessary files:

```bash
# Create and deploy optimized layer
python create_optimized_torch_layer.py
python deploy_layer.py
```

This script:
- Installs CPU-only PyTorch versions
- Removes test files, documentation, and unused modules
- Compresses aggressively
- Automatically updates your serverless.yml

## Solution 2: Container Deployment (Recommended for Large Dependencies)

Switch to AWS Lambda container images which don't have the 250MB layer limit:

```bash
# Deploy using container image
serverless deploy --config serverless-container.yml --stage prod --verbose
```

Benefits:
- No 250MB layer size limit
- Easier dependency management
- More familiar Docker workflow

## Solution 3: Minimal PyTorch Installation

If you only need specific PyTorch functionality, create a minimal layer:

### Step 1: Create minimal requirements
Create `requirements-torch-minimal.txt`:
```
torch==2.0.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
torchvision==0.15.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
```

### Step 2: Manual layer creation
```bash
# Create directory structure
mkdir -p torch_layer/python/lib/python3.10/site-packages

# Install only what you need
pip install torch==2.0.0+cpu torchvision==0.15.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --target torch_layer/python/lib/python3.10/site-packages \
    --no-deps

# Remove unnecessary files
cd torch_layer/python/lib/python3.10/site-packages
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
rm -rf torch/test torch/testing torch/_dynamo torch/profiler
rm -rf torchvision/datasets torchvision/models/detection

# Create zip
cd ../../../../
zip -r torch_layer_minimal.zip torch_layer/
```

## Current Setup Analysis

Your current serverless.yml is configured correctly:
- Uses `requirements-deploy.txt` (without PyTorch)
- References layer: `arn:aws:lambda:ap-southeast-2:216989141348:layer:custom-torch-layer:4`
- Proper package exclusions

## Recommended Next Steps

1. **Try Solution 1 first** (optimized layer):
   ```bash
   python deploy_layer.py
   ```

2. **If still too large, use Solution 2** (container):
   ```bash
   serverless deploy --config serverless-container.yml --stage prod
   ```

3. **For production**, consider Solution 2 (container deployment) as it's more maintainable and doesn't have size constraints.

## Troubleshooting

### If optimized layer is still too large:
- Check the printed size after running the script
- Consider removing more unused PyTorch modules
- Use Solution 2 (container deployment)

### If container deployment fails:
- Ensure Docker is running
- Check AWS ECR permissions
- Verify the Dockerfile builds locally:
  ```bash
  docker build -t test-image .
  ```

### Current layer size check:
```bash
# Check current layer size
unzip -l torch_layer.zip | tail -1
```

Choose the solution that best fits your deployment preferences and requirements.