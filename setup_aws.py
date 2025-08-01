import os
import subprocess
import sys
from pathlib import Path

def load_env_file(env_path):
    """Load environment variables from .env file"""
    env_vars = {}
    
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        return env_vars
        
    with open(env_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, value = line.split('=', 1)
            env_vars[key] = value
            
    return env_vars

def configure_aws_cli(env_vars):
    """Configure AWS CLI with credentials from env_vars"""
    if 'AWS_ACCESS_KEY_ID' not in env_vars or 'AWS_SECRET_ACCESS_KEY' not in env_vars:
        print("Error: AWS credentials not found in .env file")
        return False
        
    # Set AWS credentials using aws configure
    commands = [
        ['aws', 'configure', 'set', 'aws_access_key_id', env_vars['AWS_ACCESS_KEY_ID']],
        ['aws', 'configure', 'set', 'aws_secret_access_key', env_vars['AWS_SECRET_ACCESS_KEY']],
    ]
    
    if 'AWS_DEFAULT_REGION' in env_vars:
        commands.append(['aws', 'configure', 'set', 'region', env_vars['AWS_DEFAULT_REGION']])
    
    for cmd in commands:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {' '.join(cmd)}")
            print(f"Error details: {e}")
            return False
    
    print("AWS credentials configured successfully!")
    return True

if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = Path(__file__).parent.absolute()
    env_path = script_dir / '.env'
    
    # Load environment variables from .env file
    env_vars = load_env_file(str(env_path))
    
    if env_vars:
        # Configure AWS CLI
        configure_aws_cli(env_vars)