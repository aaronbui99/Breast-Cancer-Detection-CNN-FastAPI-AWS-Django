#!/usr/bin/env python3
"""
Create ECS Service
"""
import boto3
import json
import time

def create_ecs_service():
    region = "ap-southeast-2"
    account_id = "216989141348"
    
    ecs = boto3.client('ecs', region_name=region)
    ec2 = boto3.client('ec2', region_name=region)
    cf = boto3.client('cloudformation', region_name=region)
    
    # Get CloudFormation outputs
    stack = cf.describe_stacks(StackName='breast-cancer-pytorch-prod')
    outputs = {o['OutputKey']: o['OutputValue'] for o in stack['Stacks'][0]['Outputs']}
    
    print("Stack outputs:", outputs)
    
    # Create task definition
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
                "image": f"{account_id}.dkr.ecr.{region}.amazonaws.com/breast-cancer-pytorch:latest",
                "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
                "environment": [
                    {"name": "S3_BUCKET_NAME", "value": "breast-cancer-detection-api-prod-images"}
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/breast-cancer-pytorch",
                        "awslogs-region": region,
                        "awslogs-stream-prefix": "ecs"
                    }
                },
                "essential": True
            }
        ]
    }
    
    # Register task definition
    task_response = ecs.register_task_definition(**task_def)
    task_arn = task_response['taskDefinition']['taskDefinitionArn']
    print(f"Task definition created: {task_arn}")
    
    # Get default VPC and subnets
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'is-default', 'Values': ['true']}])
    if not vpcs['Vpcs']:
        vpcs = ec2.describe_vpcs()
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_ids = [s['SubnetId'] for s in subnets['Subnets'][:2]]
    
    print(f"Using VPC: {vpc_id}, Subnets: {subnet_ids}")
    
    # Create/get security group
    try:
        sg_response = ec2.create_security_group(
            GroupName='pytorch-ecs-sg',
            Description='PyTorch ECS Security Group',
            VpcId=vpc_id
        )
        sg_id = sg_response['GroupId']
        
        # Add HTTP rule
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': 'tcp',
                'FromPort': 8080,
                'ToPort': 8080,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }]
        )
    except Exception as e:
        if 'already exists' in str(e):
            sgs = ec2.describe_security_groups(
                Filters=[
                    {'Name': 'group-name', 'Values': ['pytorch-ecs-sg']},
                    {'Name': 'vpc-id', 'Values': [vpc_id]}
                ]
            )
            sg_id = sgs['SecurityGroups'][0]['GroupId']
        else:
            raise
    
    print(f"Using security group: {sg_id}")
    
    # Create service
    try:
        service_response = ecs.create_service(
            cluster="breast-cancer-pytorch-cluster",
            serviceName="pytorch-service",
            taskDefinition=task_arn,
            desiredCount=1,
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": subnet_ids,
                    "securityGroups": [sg_id],
                    "assignPublicIp": "ENABLED"
                }
            }
        )
        print("✅ ECS Service created successfully!")
    except Exception as e:
        if 'already exists' in str(e):
            print("Service exists, updating...")
            service_response = ecs.update_service(
                cluster="breast-cancer-pytorch-cluster",
                service="pytorch-service",
                taskDefinition=task_arn,
                forceNewDeployment=True
            )
        else:
            print(f"Error: {e}")
            return
    
    print("⏳ Waiting for service to stabilize...")
    time.sleep(30)
    
    # Get service endpoint
    tasks = ecs.list_tasks(cluster="breast-cancer-pytorch-cluster", serviceName="pytorch-service")
    if tasks['taskArns']:
        task_details = ecs.describe_tasks(cluster="breast-cancer-pytorch-cluster", tasks=tasks['taskArns'])
        
        for task in task_details['tasks']:
            print(f"Task status: {task['lastStatus']}")
            if task['lastStatus'] == 'RUNNING':
                for attachment in task['attachments']:
                    if attachment['type'] == 'ElasticNetworkInterface':
                        for detail in attachment['details']:
                            if detail['name'] == 'networkInterfaceId':
                                eni_id = detail['value']
                                enis = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni_id])
                                if enis['NetworkInterfaces'][0].get('Association'):
                                    public_ip = enis['NetworkInterfaces'][0]['Association']['PublicIp']
                                    endpoint = f"http://{public_ip}:8080"
                                    print(f"🎉 Service endpoint: {endpoint}")
                                    print(f"🩺 Health check: {endpoint}/health")
                                    return endpoint
    
    print("Service deployed, but endpoint not ready yet. Check back in a few minutes.")
    return None

if __name__ == "__main__":
    create_ecs_service()