#!/usr/bin/env python3
"""
Check ECS Service Status
"""
import boto3
import requests

def check_ecs_status():
    ecs = boto3.client('ecs', region_name='ap-southeast-2')
    ec2 = boto3.client('ec2', region_name='ap-southeast-2')

    print('🔍 Checking ECS service status...')
    
    # Get service status
    services = ecs.describe_services(
        cluster='breast-cancer-pytorch-cluster',
        services=['pytorch-service']
    )
    
    if services['services']:
        service = services['services'][0]
        print(f"Service status: {service['status']}")
        print(f"Running count: {service['runningCount']}")
        print(f"Desired count: {service['desiredCount']}")
    
    # Get task status
    tasks = ecs.list_tasks(cluster='breast-cancer-pytorch-cluster', serviceName='pytorch-service')
    if tasks['taskArns']:
        task_details = ecs.describe_tasks(cluster='breast-cancer-pytorch-cluster', tasks=tasks['taskArns'])
        
        for task in task_details['tasks']:
            print(f'Task status: {task["lastStatus"]}')
            print(f'Health status: {task.get("healthStatus", "UNKNOWN")}')
            
            if task['lastStatus'] == 'RUNNING':
                # Get public IP
                for attachment in task['attachments']:
                    if attachment['type'] == 'ElasticNetworkInterface':
                        for detail in attachment['details']:
                            if detail['name'] == 'networkInterfaceId':
                                eni_id = detail['value']
                                enis = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni_id])
                                if enis['NetworkInterfaces'][0].get('Association'):
                                    public_ip = enis['NetworkInterfaces'][0]['Association']['PublicIp']
                                    endpoint = f'http://{public_ip}:8080'
                                    print(f'🎉 Service endpoint: {endpoint}')
                                    print(f'🩺 Health check: {endpoint}/health')
                                    
                                    # Test the endpoint
                                    try:
                                        print('\n🧪 Testing endpoint...')
                                        response = requests.get(f'{endpoint}/health', timeout=10)
                                        if response.status_code == 200:
                                            print('✅ Health check successful!')
                                            print(response.json())
                                            return endpoint
                                        else:
                                            print(f'❌ Health check failed: {response.status_code}')
                                    except Exception as e:
                                        print(f'❌ Connection failed: {e}')
                                    
                                    return endpoint
            elif task['lastStatus'] == 'STOPPED':
                print('❌ Task stopped. Checking reason...')
                if 'stoppedReason' in task:
                    print(f'Stop reason: {task["stoppedReason"]}')
                for container in task.get('containers', []):
                    if 'reason' in container:
                        print(f'Container reason: {container["reason"]}')
    else:
        print('❌ No tasks found')
    
    return None

if __name__ == "__main__":
    endpoint = check_ecs_status()
    if endpoint:
        print(f"\n🔧 Update Lambda environment variable:")
        print(f"ECS_PYTORCH_URL={endpoint}")
    else:
        print("\n⏳ Service not ready yet. Try again in 1-2 minutes.")