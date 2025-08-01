#!/usr/bin/env python3
"""
Deploy PyTorch ECS Service
"""
import boto3
import subprocess
import os
import json
import sys

# Configuration
REGION = "ap-southeast-2"
REPO_NAME = "breast-cancer-pytorch"
IMAGE_TAG = "latest"
CLUSTER_NAME = "breast-cancer-pytorch-cluster"

def get_account_id():
    """Get AWS account ID"""
    sts = boto3.client('sts', region_name=REGION)
    return sts.get_caller_identity()['Account']

def get_ecr_uri():
    """Get ECR repository URI"""
    account_id = get_account_id()
    return f"{account_id}.dkr.ecr.{REGION}.amazonaws.com/{REPO_NAME}"

def run_command(cmd, check=True):
    """Run shell command"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        if check:
            raise
        return e

def login_to_ecr():
    """Login to ECR"""
    print("🔐 Logging into ECR...")
    cmd = f"aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {get_ecr_uri()}"
    return run_command(cmd)

def build_docker_image():
    """Build Docker image"""
    print("🐳 Building Docker image...")
    ecr_uri = get_ecr_uri()
    
    # Build image
    cmd = f"docker build -t {REPO_NAME}:{IMAGE_TAG} ./ecs-pytorch-service/"
    result = run_command(cmd)
    
    # Tag for ECR
    cmd = f"docker tag {REPO_NAME}:{IMAGE_TAG} {ecr_uri}:{IMAGE_TAG}"
    result = run_command(cmd)
    
    return ecr_uri

def push_docker_image(ecr_uri):
    """Push Docker image to ECR"""
    print("📤 Pushing Docker image to ECR...")
    cmd = f"docker push {ecr_uri}:{IMAGE_TAG}"
    return run_command(cmd)

def create_task_definition():
    """Create ECS task definition"""
    print("📋 Creating ECS task definition...")
    
    ecr_uri = get_ecr_uri()
    account_id = get_account_id()
    
    # Get role ARNs from CloudFormation stack
    cf = boto3.client('cloudformation', region_name=REGION)
    stack = cf.describe_stacks(StackName='breast-cancer-pytorch-prod')
    outputs = {o['OutputKey']: o['OutputValue'] for o in stack['Stacks'][0]['Outputs']}
    
    task_def = {
        "family": "breast-cancer-pytorch-task",
        "networkMode": "awsvpc",
        "requiresCompatibilities": ["FARGATE"],
        "cpu": "1024",
        "memory": "3072",
        "executionRoleArn": outputs['TaskExecutionRoleArn'],
        "taskRoleArn": outputs['TaskRoleArn'],
        "containerDefinitions": [
            {
                "name": "pytorch-inference",
                "image": f"{ecr_uri}:{IMAGE_TAG}",
                "portMappings": [
                    {
                        "containerPort": 8080,
                        "protocol": "tcp"
                    }
                ],
                "environment": [
                    {
                        "name": "S3_BUCKET_NAME",
                        "value": "breast-cancer-detection-api-prod-images"
                    }
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/breast-cancer-pytorch",
                        "awslogs-region": REGION,
                        "awslogs-stream-prefix": "ecs"
                    }
                },
                "essential": True
            }
        ]
    }
    
    ecs = boto3.client('ecs', region_name=REGION)
    response = ecs.register_task_definition(**task_def)
    print(f"✅ Task definition created: {response['taskDefinition']['taskDefinitionArn']}")
    return response['taskDefinition']['taskDefinitionArn']

def create_ecs_service(task_def_arn):
    """Create ECS service"""
    print("🚀 Creating ECS service...")
    
    # Get default VPC and subnets
    ec2 = boto3.client('ec2', region_name=REGION)
    
    # Get default VPC
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'is-default', 'Values': ['true']}])
    if not vpcs['Vpcs']:
        print("❌ No default VPC found. Using first available VPC.")
        vpcs = ec2.describe_vpcs()
    
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    print(f"Using VPC: {vpc_id}")
    
    # Get subnets
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_ids = [s['SubnetId'] for s in subnets['Subnets'][:2]]  # Use first 2 subnets
    print(f"Using subnets: {subnet_ids}")
    
    # Create security group for ECS service
    try:
        sg_response = ec2.create_security_group(
            GroupName='breast-cancer-pytorch-sg',
            Description='Security group for PyTorch ECS service',
            VpcId=vpc_id
        )
        sg_id = sg_response['GroupId']
        
        # Add inbound rules
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8080,
                    'ToPort': 8080,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        print(f"✅ Created security group: {sg_id}")
        
    except Exception as e:
        if 'already exists' in str(e):
            # Get existing security group
            sgs = ec2.describe_security_groups(
                Filters=[
                    {'Name': 'group-name', 'Values': ['breast-cancer-pytorch-sg']},
                    {'Name': 'vpc-id', 'Values': [vpc_id]}
                ]
            )
            sg_id = sgs['SecurityGroups'][0]['GroupId']
            print(f"✅ Using existing security group: {sg_id}")
        else:
            print(f"❌ Error creating security group: {e}")
            return None
    
    # Create ECS service
    ecs = boto3.client('ecs', region_name=REGION)
    
    service_def = {
        "serviceName": "breast-cancer-pytorch-service",
        "cluster": CLUSTER_NAME,
        "taskDefinition": task_def_arn,
        "desiredCount": 1,
        "launchType": "FARGATE",
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": subnet_ids,
                "securityGroups": [sg_id],
                "assignPublicIp": "ENABLED"
            }
        }
    }
    
    try:
        response = ecs.create_service(**service_def)
        print(f"✅ ECS service created: {response['service']['serviceName']}")
        return response['service']
    except Exception as e:
        if 'already exists' in str(e):
            print("✅ ECS service already exists, updating...")
            # Update existing service
            response = ecs.update_service(
                cluster=CLUSTER_NAME,
                service="breast-cancer-pytorch-service",
                taskDefinition=task_def_arn,
                forceNewDeployment=True
            )
            return response['service']
        else:
            print(f"❌ Error creating ECS service: {e}")
            return None

def get_service_endpoint():
    """Get ECS service endpoint"""
    print("🔍 Getting service endpoint...")
    
    ecs = boto3.client('ecs', region_name=REGION)
    ec2 = boto3.client('ec2', region_name=REGION)
    
    # Get running tasks
    tasks = ecs.list_tasks(cluster=CLUSTER_NAME, serviceName="breast-cancer-pytorch-service")
    if not tasks['taskArns']:
        print("❌ No running tasks found")
        return None
    
    # Get task details
    task_details = ecs.describe_tasks(cluster=CLUSTER_NAME, tasks=tasks['taskArns'])
    
    for task in task_details['tasks']:
        if task['lastStatus'] == 'RUNNING':
            # Get ENI details
            for attachment in task['attachments']:
                if attachment['type'] == 'ElasticNetworkInterface':
                    for detail in attachment['details']:
                        if detail['name'] == 'networkInterfaceId':
                            eni_id = detail['value']
                            
                            # Get public IP
                            enis = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni_id])
                            if enis['NetworkInterfaces'][0].get('Association'):
                                public_ip = enis['NetworkInterfaces'][0]['Association']['PublicIp']
                                endpoint = f"http://{public_ip}:8080"
                                print(f"✅ Service endpoint: {endpoint}")
                                return endpoint
    
    print("❌ Could not find service endpoint")
    return None

def main():
    """Main deployment function"""
    print("🚀 Deploying PyTorch ECS Service")
    print("=" * 50)
    
    try:
        # Step 1: Login to ECR
        login_to_ecr()
        
        # Step 2: Build Docker image
        ecr_uri = build_docker_image()
        
        # Step 3: Push to ECR
        push_docker_image(ecr_uri)
        
        # Step 4: Create task definition
        task_def_arn = create_task_definition()
        
        # Step 5: Create ECS service
        service = create_ecs_service(task_def_arn)
        
        if service:
            print("\n⏳ Waiting for service to start (this may take 2-3 minutes)...")
            print("Use this command to check status:")
            print(f"aws ecs describe-services --cluster {CLUSTER_NAME} --services breast-cancer-pytorch-service --region {REGION}")
            
            # Try to get endpoint after a short wait
            import time
            time.sleep(30)
            endpoint = get_service_endpoint()
            
            if endpoint:
                print(f"\n🎉 Deployment complete!")
                print(f"🔗 Service URL: {endpoint}")
                print(f"🩺 Health check: {endpoint}/health")
                print(f"\nNext: Update Lambda environment variable:")
                print(f"ECS_PYTORCH_URL={endpoint}")
                return endpoint
            else:
                print("\n⚠️ Service deployed but endpoint not ready yet.")
                print("Check back in a few minutes.")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()