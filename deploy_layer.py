import subprocess
import json
import os
from create_optimized_torch_layer import create_optimized_torch_layer

def deploy_layer():
    """Deploy the optimized PyTorch layer to AWS Lambda"""
    
    # Create the optimized layer
    layer_zip = create_optimized_torch_layer()
    
    # Upload to S3
    s3_bucket = "breast-cancer-detection-api-prod-images"  # Your S3 bucket
    s3_key = f"lambda-layers/{layer_zip}"
    
    print(f"Uploading {layer_zip} to S3...")
    subprocess.run([
        "aws", "s3", "cp", layer_zip, f"s3://{s3_bucket}/{s3_key}"
    ], check=True)
    
    # Publish the layer version
    print("Publishing layer version...")
    result = subprocess.run([
        "aws", "lambda", "publish-layer-version",
        "--layer-name", "custom-torch-layer",
        "--content", f"S3Bucket={s3_bucket},S3Key={s3_key}",
        "--compatible-runtimes", "python3.10",
        "--region", "ap-southeast-2"
    ], capture_output=True, text=True, check=True)
    
    layer_info = json.loads(result.stdout)
    layer_arn = layer_info['LayerVersionArn']
    version = layer_info['Version']
    
    print(f"Layer published successfully!")
    print(f"Layer ARN: {layer_arn}")
    print(f"Version: {version}")
    
    # Update serverless.yml with new layer version
    update_serverless_config(layer_arn, version)
    
    return layer_arn, version

def update_serverless_config(layer_arn, version):
    """Update serverless.yml with the new layer version"""
    serverless_file = "serverless.yml"
    
    with open(serverless_file, 'r') as f:
        content = f.read()
    
    # Replace the old layer ARN with the new one
    old_pattern = "arn:aws:lambda:ap-southeast-2:216989141348:layer:custom-torch-layer:"
    
    # Find the line with the layer and update it
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if old_pattern in line:
            lines[i] = f"      - {layer_arn}"
            break
    
    updated_content = '\n'.join(lines)
    
    with open(serverless_file, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated serverless.yml with new layer version: {version}")

if __name__ == "__main__":
    try:
        deploy_layer()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("If the layer is still too large, consider using Solution 2 (container deployment)")