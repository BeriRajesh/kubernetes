import boto3
import os
import json
import traceback
import time
import sys

#main_payload = {"cluster" : "prod-1", "container_name" : "audiencebuilder-prod", "taskDefinition" : "audiencebuilder-prod", "cpu" : 20, "memory" : 256, "memoryReservation" : 128, "command_with_args": ["python","lib/deploy.py"]}

client = boto3.client('ecs')

def get_service() -> dict:
    print(f"{ECS_CLUSTER=}")
    print(f"{SERVICE_NAME=}")
    service_description = client.describe_services(
        cluster=ECS_CLUSTER,
        services=[
            SERVICE_NAME,
        ]
    )
    # print(f"{service_description=}")
    service = None
    if services := service_description.get('services'):
        service = services[0]

    return service

def get_task_environment(launch_type: str) -> dict:
    """Returns environment (dict) = task_definition's + overrides from task"""

    global TASK_DEFINITION_LOG_GROUP, TASK_DEFINITION_LOG_PREFIX

    task_definition_description = client.describe_task_definition(
        taskDefinition=TASK_DEFINITION_NAME,
    )

    environment = None
    log_configuration = None
    for container_definition in task_definition_description['taskDefinition'].get('containerDefinitions'):
        if container_definition['name'] == CONTAINER_NAME:
            environment = container_definition.get('environment')
            log_configuration = container_definition.get('logConfiguration')
            break

    TASK_DEFINITION_LOG_GROUP = []
    TASK_DEFINITION_LOG_PREFIX = []
    try:
        TASK_DEFINITION_LOG_GROUP = log_configuration['options']['awslogs-group']
        TASK_DEFINITION_LOG_PREFIX = log_configuration['options']['awslogs-stream-prefix']
    except:
        traceback.print_exc()

    # check for environment overrides
    task_list = client.list_tasks(
        cluster=ECS_CLUSTER,
        serviceName=SERVICE_NAME,
        desiredStatus='RUNNING',
        launchType=launch_type
    )

    taskArns = task_list.get('taskArns', [])
    if taskArns:
        task_descriptions = client.describe_tasks(
            cluster=ECS_CLUSTER,
            tasks=taskArns,
        )
        # print('task_descriptions:', json.dumps(task_descriptions, indent=4, default=str))

        environment_override = None
        for task in task_descriptions['tasks']:
            for override in task.get('overrides', {}).get('containerOverrides', []):
                if override.get('name') != TASK_NAME:
                    continue

                environment_override = override.get('environment', {})
                break

            if environment_override:
                environment.update(environment_override)
                break

    return environment or []

def execute_sql_deploy_command() -> str:
    """ Executes sql_deploy_command using ecs.run_task()

    Returns task_arn: ARN of the task executing the sql deploy command"""

    params = dict()

    service = get_service()

    launch_type = None
    if service:
        launch_type = service['launchType']

        environment = get_task_environment(launch_type)
        sql_deploy_command = SQL_DEPLOY_COMMAND

        params = dict(
            cluster=ECS_CLUSTER,
            taskDefinition=TASK_DEFINITION_NAME,
            count=1,
            launchType=launch_type,
            enableExecuteCommand=True,
            overrides={
                'containerOverrides': [{
                    'name': f'{CONTAINER_NAME}',
                    'command': sql_deploy_command,
                    'environment': environment,
                }]
            }
        )

        if launch_type == 'FARGATE':
            network_configuration = service['networkConfiguration']
            params.update(dict(
                networkConfiguration=network_configuration
        ))

    print('Executing sql_deploy_command in ECS container with params', json.dumps(params, indent=4, default=str))

    response = client.run_task(**params)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print('Response from ECS: OK')
    else:
        print('Response from ECS:', json.dumps(response, indent=4, default=str))

    task_arn = response['tasks'][0]['taskArn']
    print(f"{task_arn=}")

    return task_arn


def monitor_task(task_arn: str) -> bool:
    """ Monitor the task execution

    Return True on Success, False if exit code > 0 for sql deploy task

    Raises TimeoutError
    """

    time_begin = time.time()
    timeout = 10*60
    wait_time = 5

    last_status = None
    task_description = None
    while task_description is None or last_status != 'STOPPED':
        task_description = client.describe_tasks(
            cluster=ECS_CLUSTER,
            tasks=[
                task_arn,
            ],
        )
        # print(json.dumps(task_description, indent=4, default=str))
        last_status = task_description['tasks'][0]['lastStatus']
        print(f'{last_status=}', flush=True)

        if time.time() - time_begin > timeout:
            print('Timeout reached!', flush=True)
            raise TimeoutError
            break

        print(f'Waiting {wait_time}s ...', flush=True)
        time.sleep(wait_time)

    failures = task_description.get('failures')

    exit_code = None
    reason = None
    for container in task_description['tasks'][0]['containers']:
        print(f'{container.get("name")=} {container.get("exitCode")=}')
        if container.get('name') == SERVICE_NAME:
            exit_code = container.get('exitCode')
            reason = container.get('reason')
            print(f'{exit_code=}, {reason=}')
            print(json.dumps(container, indent=4, default=str))
            break

    if failures or exit_code:
        return False

    return True

def get_test_command() -> list:
    """Returns test command as a list"""

    command = ["python3", "-c", "import boto3; import time; client=boto3.client('sts');caller=client.get_caller_identity();print(caller, flush=True); time.sleep(10)"]

    return command

def get_sql_deploy_command() -> list:
    """ Returns sql_deploy_command or a test sql_deploy_command"""

    sql_deploy_command = os.environ.get("SQL_DEPLOY_COMMAND").split(" ")
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        sql_deploy_command = get_test_command()

    return sql_deploy_command

def get_task_log_lines(task_arn: str) -> list:
    """ Returns list of log lines for task """

    logs_client = boto3.client('logs')

    log_lines = []
    task_id = task_arn.split('/')[-1]
    params = dict(
        logGroupName=TASK_DEFINITION_LOG_GROUP,
        logStreamName=f'{TASK_DEFINITION_LOG_PREFIX}/{CONTAINER_NAME}/{task_id}',
        startFromHead=True
    )
    print('Getting log from SQL_DEPLOY task with params', json.dumps(params, indent=4, default=str))
    response = logs_client.get_log_events(**params)

    events = response.get('events')
    for event in events:
        log_lines.append(event.get('message'))

    return log_lines

def main():
    task_arn = execute_sql_deploy_command()
    result = monitor_task(task_arn)

    log_lines = get_task_log_lines(task_arn)
    print('================ SQL DEPLOY TASK LOG =====================')
    print("\n".join(log_lines))
    print('==========================================================')

    if not result:
        print('==========================================================')
        print()
        print("ERROR in SQL DEPLOY script")
        print()
        print('==========================================================')
        traceback.print_exc()
        raise RuntimeError(f'Please see logs for task ARN: {task_arn} in cluster {ECS_CLUSTER}')

    print('Execution of SQL_DEPLOY_COMMAND was succcessful')
    return True


if __name__ == "__main__":
    try:
        SQL_DEPLOY_COMMAND = get_sql_deploy_command()

        ECS_CLUSTER = os.environ.get("ECS_CLUSTER")
        APP_NAME =  os.environ.get("APP_NAME")
        BUILD_ENV = os.environ.get("BUILD_ENV")
        TASK_DEFINITION_NAME = f"{APP_NAME}-{BUILD_ENV}"
        CONTAINER_NAME = TASK_DEFINITION_NAME
        SERVICE_NAME = TASK_DEFINITION_NAME
        TASK_NAME = TASK_DEFINITION_NAME

        TASK_DEFINITION_LOG_GROUP = None # to be determined later
        TASK_DEFINITION_LOG_PREFIX = None  # to be determined later

        if main():
            sys.exit(0)

    except TimeoutError:
        raise TimeoutError
    # except:
        # traceback.print_exc()
        # print("Ignoring error, continuing.")