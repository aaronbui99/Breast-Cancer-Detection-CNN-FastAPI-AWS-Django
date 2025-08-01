#!/usr/bin/env python3
"""
Script to find publicly available PyTorch layers in AWS Lambda
"""
import boto3
import json
from botocore.exceptions import ClientError

def find_pytorch_layers():
    """Find PyTorch layers in different AWS regions"""
    
    # Common regions where public layers are available
    regions = [
        'us-east-1',      # N. Virginia (most common for public layers)
        'us-west-2',      # Oregon
        'ap-southeast-2', # Sydney (your region)
        'eu-west-1',      # Ireland
        'us-west-1',      # N. California
    ]
    
    # Known public PyTorch layer ARNs to check
    known_pytorch_layers = [
        # PyTorch layers from various sources
        "arn:aws:lambda:us-east-1:898466741470:layer:psycopg2-py38:1",
        "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:1",
        "arn:aws:lambda:us-east-1:626072310623:layer:torch-py39:1",
        "arn:aws:lambda:us-east-1:446751924810:layer:python-3-8-scikit-learn-0-23-1:2",
        "arn:aws:lambda:us-west-2:420165488524:layer:AWSLambda-Python38-SciPy1x:37",
        # Add more known ARNs here
    ]
    
    results = {}
    
    for region in regions:
        print(f"\n🔍 Searching in region: {region}")
        results[region] = []
        
        try:
            # Create Lambda client for this region
            lambda_client = boto3.client('lambda', region_name=region)
            
            # List layers in this region
            response = lambda_client.list_layers(MaxItems=50)
            layers = response.get('Layers', [])
            
            # Filter for PyTorch-related layers
            pytorch_layers = []
            for layer in layers:
                layer_name = layer['LayerName'].lower()
                if any(keyword in layer_name for keyword in ['torch', 'pytorch', 'ml', 'ai', 'deep']):
                    pytorch_layers.append(layer)
                    print(f"  ✅ Found: {layer['LayerName']} - {layer['LatestMatchingVersion']['LayerVersionArn']}")
            
            results[region] = pytorch_layers
            
            if not pytorch_layers:
                print(f"  ❌ No PyTorch layers found in {region}")
                
        except ClientError as e:
            print(f"  ❌ Error searching {region}: {e}")
            continue
    
    return results

def check_specific_layers():
    """Check specific known PyTorch layer ARNs"""
    
    # Known public PyTorch layers (these may change over time)
    known_layers = {
        "us-east-1": [
            "arn:aws:lambda:us-east-1:626072310623:layer:torch:1",
            "arn:aws:lambda:us-east-1:626072310623:layer:torch-py39:1", 
            "arn:aws:lambda:us-east-1:626072310623:layer:torch-py38:1",
            "arn:aws:lambda:us-east-1:898466741470:layer:pytorch-py38:1",
        ],
        "us-west-2": [
            "arn:aws:lambda:us-west-2:420165488524:layer:AWSLambda-Python38-SciPy1x:37",
            "arn:aws:lambda:us-west-2:626072310623:layer:torch:1",
        ],
        "ap-southeast-2": [
            # Usually fewer public layers in non-US regions
        ]
    }
    
    print("\n🧪 Checking specific known PyTorch layers...")
    
    for region, layer_arns in known_layers.items():
        if not layer_arns:
            continue
            
        print(f"\n📍 Region: {region}")
        lambda_client = boto3.client('lambda', region_name=region)
        
        for layer_arn in layer_arns:
            try:
                # Try to get layer version info
                response = lambda_client.get_layer_version_by_arn(Arn=layer_arn)
                print(f"  ✅ AVAILABLE: {layer_arn}")
                print(f"     Description: {response.get('Description', 'N/A')}")
                print(f"     Compatible Runtimes: {response.get('CompatibleRuntimes', [])}")
                print(f"     Size: {response.get('Content', {}).get('CodeSize', 'Unknown')} bytes")
                
            except ClientError as e:
                if 'ResourceNotFoundException' in str(e):
                    print(f"  ❌ NOT FOUND: {layer_arn}")
                else:
                    print(f"  ❌ ERROR: {layer_arn} - {e}")

def generate_serverless_config(layer_arn):
    """Generate serverless.yml configuration for a PyTorch layer"""
    
    config = f"""
# Add this to your serverless.yml functions section:

functions:
  api:
    handler: app.main.handler
    events:
      - http:
          path: /{{proxy+}}
          method: any
          private: true
    layers:
      - {{Ref: PythonRequirementsLambdaLayer}}
      - {layer_arn}  # PyTorch layer
    environment:
      PYTHONPATH: /opt/python:/var/runtime:/var/task
"""
    
    return config

if __name__ == "__main__":
    print("🔍 Searching for PyTorch layers in AWS Lambda...")
    
    # Search for layers
    results = find_pytorch_layers()
    
    # Check specific known layers
    check_specific_layers()
    
    # Print summary
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    found_any = False
    for region, layers in results.items():
        if layers:
            found_any = True
            print(f"\n🌍 {region}:")
            for layer in layers:
                arn = layer['LatestMatchingVersion']['LayerVersionArn']
                print(f"  📦 {layer['LayerName']}: {arn}")
    
    if not found_any:
        print("\n❌ No PyTorch layers found in searched regions.")
        print("\n💡 Recommendations:")
        print("1. Create your own PyTorch layer")
        print("2. Use AWS SageMaker for ML workloads")
        print("3. Switch to ECS/Fargate containers")
        print("4. Use AWS Batch for large workloads")
    
    print(f"\n📝 To use a layer, add it to your serverless.yml:")
    print(generate_serverless_config("arn:aws:lambda:REGION:ACCOUNT:layer:LAYER_NAME:VERSION"))
    
    print("\n🔗 Useful resources:")
    print("- Klayers (public layers): https://github.com/keithrozario/Klayers")
    print("- AWS Lambda Layers: https://aws.amazon.com/lambda/layers/")
    print("- Serverless Framework layers: https://www.serverless.com/framework/docs/providers/aws/guide/layers")