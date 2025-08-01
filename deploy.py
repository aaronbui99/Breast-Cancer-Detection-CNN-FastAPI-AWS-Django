import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and print its output"""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        return False

def check_prerequisites():
    """Check if all prerequisites are installed"""
    prerequisites = [
        ("node", "Node.js is not installed. Please install it from https://nodejs.org/"),
        ("npm", "npm is not installed. It should come with Node.js"),
        ("serverless", "Serverless Framework is not installed. Run 'npm install -g serverless'"),
        ("aws", "AWS CLI is not installed. Please install it from https://aws.amazon.com/cli/")
    ]
    
    for cmd, error_msg in prerequisites:
        try:
            subprocess.run(f"where {cmd}", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            print(f"Error: {error_msg}")
            return False
    
    return True

def setup_aws_credentials():
    """Set up AWS credentials from .env file"""
    script_dir = Path(__file__).parent.absolute()
    setup_script = script_dir / 'setup_aws.py'
    
    if not os.path.exists(setup_script):
        print("Error: setup_aws.py script not found")
        return False
    
    return run_command(f"python {setup_script}", "Setting up AWS credentials")

def install_serverless_plugins():
    """Install required Serverless plugins"""
    return run_command("npm install --save-dev serverless-python-requirements", "Installing Serverless plugins")

def deploy_to_aws():
    """Deploy the application to AWS using Serverless Framework"""
    return run_command("serverless deploy --verbose", "Deploying to AWS")

def main():
    """Main deployment function"""
    print("=== Breast Cancer Detection API Deployment ===")
    
    # Check prerequisites
    if not check_prerequisites():
        print("Please install the missing prerequisites and try again.")
        return
    
    # Setup AWS credentials
    if not setup_aws_credentials():
        print("Failed to set up AWS credentials. Please check your .env file.")
        return
    
    # Install Serverless plugins
    if not install_serverless_plugins():
        print("Failed to install Serverless plugins.")
        return
    
    # Deploy to AWS
    if not deploy_to_aws():
        print("Deployment failed. Please check the error messages above.")
        return
    
    print("\n=== Deployment completed successfully! ===")
    print("Your API is now available through the API Gateway URL shown above.")

if __name__ == "__main__":
    main()