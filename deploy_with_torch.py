import os
import subprocess
import sys
import argparse

def run_command(command):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode == 0

def deploy():
    """Deploy the application with PyTorch support"""
    parser = argparse.ArgumentParser(description="Deploy the breast cancer detection API")
    parser.add_argument("--create-layer", action="store_true", help="Create a PyTorch Lambda layer")
    parser.add_argument("--layer-arn", help="ARN of the PyTorch Lambda layer")
    args = parser.parse_args()
    
    # Step 1: Create PyTorch layer if requested
    if args.create_layer:
        print("Creating PyTorch Lambda layer...")
        if not run_command(f"{sys.executable} create_torch_layer.py"):
            print("Failed to create PyTorch layer")
            return False
        
        print("\nNow upload the torch_layer.zip file to AWS Lambda as a layer.")
        print("After uploading, run this script again with the --layer-arn parameter.")
        return True
    
    # Step 2: Update serverless.yml with the layer ARN if provided
    if args.layer_arn:
        print(f"Updating serverless.yml with PyTorch layer ARN: {args.layer_arn}")
        with open("serverless.yml", "r") as f:
            content = f.read()
        
        # Replace the commented layer line with the actual ARN
        content = content.replace(
            "# - arn:aws:lambda:ap-southeast-2:ACCOUNT_ID:layer:pytorch:1",
            f"- {args.layer_arn}"
        )
        
        with open("serverless.yml", "w") as f:
            f.write(content)
    
    # Step 3: Deploy with serverless
    print("Deploying with Serverless Framework...")
    if not run_command("serverless deploy"):
        print("Deployment failed")
        return False
    
    print("\nDeployment completed successfully!")
    print("To test the API, run: serverless info")
    return True

if __name__ == "__main__":
    deploy()