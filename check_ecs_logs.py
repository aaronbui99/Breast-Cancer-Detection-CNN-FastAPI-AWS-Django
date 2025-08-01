#!/usr/bin/env python3
"""
Check ECS Logs
"""
import boto3
import time

def check_ecs_logs():
    ecs = boto3.client('ecs', region_name='ap-southeast-2')
    logs = boto3.client('logs', region_name='ap-southeast-2')
    
    print('🔍 Checking ECS events and logs...')
    
    # Get service events
    services = ecs.describe_services(
        cluster='breast-cancer-pytorch-cluster',
        services=['pytorch-service']
    )
    
    if services['services']:
        service = services['services'][0]
        print(f"Service status: {service['status']}")
        print(f"Running: {service['runningCount']}, Pending: {service['pendingCount']}, Desired: {service['desiredCount']}")
        
        print('\n📋 Recent service events:')
        for event in service['events'][:5]:
            print(f"  {event['createdAt']}: {event['message']}")
    
    # Check CloudWatch logs
    try:
        log_streams = logs.describe_log_streams(
            logGroupName='/ecs/breast-cancer-pytorch',
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if log_streams['logStreams']:
            print('\n📝 Recent log streams:')
            for stream in log_streams['logStreams']:
                print(f"  {stream['logStreamName']} - Last event: {stream.get('lastEventTime', 'No events')}")
                
                # Get recent log events
                try:
                    events = logs.get_log_events(
                        logGroupName='/ecs/breast-cancer-pytorch',
                        logStreamName=stream['logStreamName'],
                        limit=10
                    )
                    
                    if events['events']:
                        print(f"    Recent logs:")
                        for event in events['events'][-5:]:
                            print(f"      {event['message'].strip()}")
                except Exception as e:
                    print(f"    Could not get logs: {e}")
        else:
            print('\n📝 No log streams found yet')
            
    except Exception as e:
        print(f'\n📝 Could not access logs: {e}')

if __name__ == "__main__":
    check_ecs_logs()