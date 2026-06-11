""" script to trigger a codebuild project """

import os
from pprint import pprint
import sys
import time
import json
import boto3

CLUSTER_NAME = os.environ.get("CLUSTER_NAME", 'dev-1')
CONTAINER_COUNT = os.environ.get("CONTAINER_COUNT", 1)
LAUNCH_TYPE = os.environ.get("LAUNCH_TYPE", 'FARGATE')
CPU_LIMIT = os.environ.get("CPU_LIMIT", '1024')
MEMORY_LIMIT = os.environ.get("MEMORY_LIMIT", '2048')
STORAGE_LIMIT = os.environ.get("STORAGE_LIMIT", 50)
TASK_DEFINITION = os.environ.get("TASK_DEFINITION", 'docker-image-builder')
SUBNETS = os.environ.get("SUBNETS", ["subnet-bea3d096"])
SECURITY_GROUPS = os.environ.get("SECURITY_GROUPS", ["sg-09c57428a89f57f51"])
ASSIGN_PUBLICIP = os.environ.get("ASSIGN_PUBLICIP", 'DISABLED')
CONTAINER_NAME_IN_TASK_DEF = os.environ.get("CONTAINER_NAME", 'docker-image-builder')
PROPAGATE_TAGS = os.environ.get("PROPAGATE_TAGS", 'TASK_DEFINITION')
ENABLE_EXECUTE_COMMAND = os.environ.get("ENABLE_EXECUTE_COMMAND", True)
GIT_REPO = os.environ.get("GIT_REPO", '')
CONTEXT_SUB_FOLDER = os.environ.get("CHANGE_PATH", '')
DOCKERFILE = os.environ.get("DOCKERFILE", 'Dockerfile')
ECR_REPOSITORY_URI = os.environ.get("ECR_REPOSITORY_URI", '')
IMAGE_TAG = os.environ.get("IMAGE_TAG", 'latest')
VERSION_TAG = os.environ.get("VERSION_TAG", IMAGE_TAG if os.environ.get("VERSION_TAG") == '' else os.environ.get("IMAGE_TAG", 'null_version'))
KANIKO_ADDITIONAL_ARGS = os.environ.get("KANIKO_ADDITIONAL_ARGS", '') # "--force, --no-push, --verbosity=debug"


ecs_client = boto3.client('ecs')
logs_client = boto3.client('logs')

# Create ECS Fargate task to run Kaniko and build container inage
response = ecs_client.run_task(
    cluster=CLUSTER_NAME,
    count=CONTAINER_COUNT,
    enableExecuteCommand=ENABLE_EXECUTE_COMMAND,
    launchType=LAUNCH_TYPE,
    networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': SUBNETS,
            'securityGroups': SECURITY_GROUPS,
            'assignPublicIp': ASSIGN_PUBLICIP
        }
    },
    overrides={
        'containerOverrides': [
            {
                'name': CONTAINER_NAME_IN_TASK_DEF,
                'command': [
                    "--context", GIT_REPO,
                    "--context-sub-path", CONTEXT_SUB_FOLDER,
                    "--dockerfile", DOCKERFILE,
                    "--destination", ECR_REPOSITORY_URI + ':' + IMAGE_TAG,
                    "--destination", ECR_REPOSITORY_URI + ':' + VERSION_TAG,
                    KANIKO_ADDITIONAL_ARGS
                ]
            },
        ],
        'cpu': CPU_LIMIT,
        'memory': MEMORY_LIMIT,
        'ephemeralStorage': {
            'sizeInGiB': STORAGE_LIMIT
        }
    },
    propagateTags=PROPAGATE_TAGS,
    taskDefinition=TASK_DEFINITION
)

# Extract task ID from ECS Run Task response
if 'tasks' in response and len(response['tasks']) > 0:
    task_arn = response['tasks'][0]['taskArn']
    print(f'Task Arn: {task_arn}')
    task_id = response['tasks'][0]['taskArn'].split('/')[-1]
    print(f'Task ID: {task_id}')

    # Fetch LogGroup and LogStream name from TASK_DEF
    task_def = ecs_client.describe_task_definition(taskDefinition=TASK_DEFINITION)
    log_config = task_def['taskDefinition']['containerDefinitions'][0].get('logConfiguration', None)
    container_name = task_def['taskDefinition']['containerDefinitions'][0].get('name', None)
    log_group_name = log_config['options'].get('awslogs-group', '/aws/ecs/docker_image_builder')
    log_stream_prefix = log_config['options'].get('awslogs-stream-prefix', 'docker_image_builder')
    log_stream_name = f'{log_stream_prefix}/{container_name}/{task_id}'
    print(f'Sending logs to Log group {log_group_name}')
    print(f'Logs are stream in {log_stream_name}')

    prev_task_status = ''
    while True:
        task_describe = ecs_client.describe_tasks(
            cluster=CLUSTER_NAME,
            tasks=[task_arn]
        )
        task_status = task_describe['tasks'][0]['lastStatus']
        if task_status != prev_task_status:
            print('Task current status is {}'.format(task_status), flush=True)

        if task_status == 'RUNNING':
            try:
                log_events = logs_client.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=log_stream_name,
                    startFromHead=True
                )
                for event in log_events['events']:
                    print(event['message'])

                next_forward_token = log_events['nextForwardToken']

                time.sleep(10)
            except Exception as e:
                print(f'Error fetching logs: {str(e)}')
                time.sleep(10)
        
        elif task_status == 'STOPPED' or task_status == 'DEAD':
            containers = task_describe['tasks'][0].get('containers', [])
            if containers:
                for container in containers:
                    if 'exitCode' in container:
                        exit_code = container['exitCode']
                        print(f'Task exit code: {exit_code}')
                        if exit_code != 0:
                            print('Exited with non-zero exit code (failure). Check logs for more details.')
                            sys.exit(exit_code)
            else:
                print('Exited with non-zero exit code (failure). Check logs for more details.')
                sys.exit(1)
            break
        prev_task_status = task_status
else:
    print(f'No tasks were started.')
