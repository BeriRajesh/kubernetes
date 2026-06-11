""" script to trigger a codebuild project """

import os
from pprint import pprint
import sys
import time
import json

import boto3


# Developers to control the deployment in Dev environment using buildspec.yml:
    # GRUNT_MINIFY_CODE="true|false"
    # MINIFY_CODE="true|false"
    # INTEGRATION_TEST="true|false"
    # UNIT_TEST="true|false"
    # REGRESSION_TEST="true|false"
    # PERFORMANCE_TEST="true|false"
    # SANITY_TEST="true|false"
    # getCodeVersion=true|false: to generate a __version file. default to false
    # DEPLOY_CODE="true|false"
    # SQL_DEPLOY_COMMAND="python example.py" # this command is specified by devs in .buildspec.yaml

    #export POST_BUILD_QA_SANITY_TEST="false"

# Bamboo to override codebuild env variables for Dev Environment:
    # CODEBUILD_PROJECT_NAME="<codebuild project name>"
    # BUILD_ENV="dev"
    # ECS_CLUSTER="andems-dev"
    # ECS_SERVICE_NAME="<ecs service name>"
    # LAMBDA_FUNCTION_NAME="<lambda function name if not as app_name-build_env>"
    # ECS_TASK_FAMILY="<ecs task family name>"
    # IMAGE_TAG="latest-develop"


# Bamboo to override codebuild env variables for non-dev environments:
    # CODEBUILD_PROJECT_NAME="<codebuild project name>"
    # BUILD_ENV="qa|stg|prod"
    # ECS_CLUSTER="<ecs cluster name>"
    # ECS_SERVICE_NAME="<ecs service name>"
    # LAMBDA_FUNCTION_NAME="<lambda function name if not as app_name-build_env>"
    # ECS_TASK_FAMILY="<ecs task family name>"
    # IMAGE_TAG=latest-qa|latest-staging|latest-prod
    # DEPLOY_CODE="true|false"
    # SERVEROVERRIDE_KEY="true|false"
    # MINIFY_CODE="true|false"
    # GRUNT_MINIFY_CODE="true|false"
    # INTEGRATION_TEST="true|false"
    # UNIT_TEST="true|false"
    # REGRESSION_TEST="true|false"
    # PERFORMANCE_TEST="true|false"

# environment variable set up in Bamboo plan
CODEBUILD_PROJECT_NAME = os.environ.get("CODEBUILD_PROJECT_NAME") # ex:= <projectname>
COMMIT_ID              = os.environ.get("COMMIT_ID", "develop")

BUILD_ENV = os.environ.get("BUILD_ENV", "dev")
USE_IMAGE_CACHING = os.environ.get("USE_IMAGE_CACHING", "true")


# these variables will be sent to codebuild's environment
# var_name: default_value
variables_for_codebuild = {
    'BUILD_ENV': BUILD_ENV,
    'IMAGE_TAG': os.environ.get("IMAGE_TAG", "latest-develop"),
    'getCodeVersion': os.environ.get("getCodeVersion", ''),
    'INTEGRATION_TEST': os.environ.get("INTEGRATION_TEST", ''),
    'UNIT_TEST': os.environ.get("UNIT_TEST", ''),
    'REGRESSION_TEST': os.environ.get("REGRESSION_TEST", ''),
    'SANITY_TEST': os.environ.get("SANITY_TEST", ''),
    'API_TEST': os.environ.get("API_TEST", ''),
    'POST_BUILD_QA_REGRESSION_TEST': os.environ.get("POST_BUILD_QA_REGRESSION_TEST", ''),
    'PERFORMANCE_TEST': os.environ.get("PERFORMANCE_TEST", ''),
    'GRUNT_MINIFY_CODE': os.environ.get("GRUNT_MINIFY_CODE", ''),
    'MINIFY_CODE': os.environ.get("MINIFY_CODE", ''),
    'DEPLOY_CODE': os.environ.get("DEPLOY_CODE", ''),
    'SQL_DEPLOY': os.environ.get("SQL_DEPLOY", ''),
    'ECS_CLUSTER': os.environ.get("ECS_CLUSTER","andems-dev"),
    'ECS_SERVICE_NAME': os.environ.get("ECS_SERVICE_NAME", ''),
    'LAMBDA_FUNCTION_NAME': os.environ.get("LAMBDA_FUNCTION_NAME", ''),
    'ECS_TASK_FAMILY': os.environ.get("ECS_TASK_FAMILY", ''),
    'SERVEROVERRIDE_KEY': os.environ.get("SERVEROVERRIDE_KEY", ''),# addded for reportbuilder 'flask db upgrad'
    'S3_DEPLOY_BUCKET': os.environ.get("S3_DEPLOY_BUCKET", ''),# addded for Mena orchestrate S3 Deploymen'
    'CF_DISTRIBUTION_ID': os.environ.get("CF_DISTRIBUTION_ID", ''),# addded for Mena orchestrate CF Invalidatio'
    'TAG_OVERRIDES': os.environ.get("TAG_OVERRIDES", ''),
    'PARAMETERS_OVERRIDES': os.environ.get("PARAMETERS_OVERRIDES", ''),
    'RUN_SECRET_ENTRYPOINT': os.environ.get("RUN_SECRET_ENTRYPOINT", ''),
    'USE_IMAGE_CACHING': os.environ.get("USE_IMAGE_CACHING", ''),
    'DOCKER_LAMBDA': os.environ.get("DOCKER_LAMBDA", ''),
    'DEPLOY_ROLE': os.environ.get("DEPLOY_ROLE", ''),
    'COMMIT_HASH': os.environ.get("COMMIT_HASH", ''), #added for ecr image tag
    'DB_COMMAND': os.environ.get("DB_COMMAND", ''), #DB Command override
    'DB_DEPLOY_URI': os.environ.get("DB_DEPLOY_URI", ''), #API URI for Lambda SQL Deploy
    'SQL_DEPLOY_TOKEN_PATH': os.environ.get("SQL_DEPLOY_TOKEN_PATH", ''), #SSM path for SQL Deploy Token

    # 2022-09-22 - cdn changes
    'SOURCE_BUILD_PATH': os.environ.get("SOURCE_BUILD_PATH", ''),
    'S3_DEPLOY_PATH': os.environ.get("S3_DEPLOY_PATH", ''),
    'INVALIDATE_CACHE': os.environ.get("INVALIDATE_CACHE", ''),
    'INVALIDATION_PATH': os.environ.get("INVALIDATION_PATH", ''),
    'CF_DISTRIBUTION_ID': os.environ.get("CF_DISTRIBUTION_ID", ''),
    'ECR_ACCOUNT_ID': os.environ.get("ECR_ACCOUNT_ID", ''),
    'ECR_REPO': os.environ.get("ECR_REPO", ''),
    'CHANGED_PATH': os.environ.get("CHANGED_PATH", ''),
    'ECR_REGION': os.environ.get("ECR_REGION", ''),
    
    # 2024-03-04
    'DOCKERFILE_RELATIVE_PATH': os.environ.get("DOCKERFILE_RELATIVE_PATH", "Dockerfile"),

}
environment_variables = [{'name': var_name, 'value': variables_for_codebuild[var_name]} for var_name in variables_for_codebuild.keys()]

def filter_function(dict_obj):
    """Filters keys with false-ish values like '' or None from dict_obj"""
    key, value = dict_obj.items()
    if dict_obj["value"] != '' and dict_obj["value"] is not None:
        return True
    return False

environment_variables = list(filter(filter_function, environment_variables))
pprint(environment_variables)

codebuild = boto3.client('codebuild')


# launch project
response = codebuild.start_build_batch(
    projectName=CODEBUILD_PROJECT_NAME,
    environmentVariablesOverride=environment_variables,
    sourceVersion=COMMIT_ID
)

build_id = response["buildBatch"]["id"]

build_status = None
while True:
    response = codebuild.batch_get_build_batches(
        ids=[build_id]
    )
    # print(f'{build_id=}')
    try:
        buildGroups = response['buildBatches'][0]['buildGroups']
        last_build_group = buildGroups[-1]
        streamName = last_build_group.get('currentBuildSummary', {}).get('arn').split(':')[-1]
        print('Build status is {}'.format(build_status), flush=True)
        if streamName:
            print(f'Some logs are pushed to Loggly. You can try searching in Loggly within "All Sources" using the search term --> tag:{streamName} <--')
        else:
            print('Streamname could not be detected from response.')
            # print(json.dumps(response, indent=4, default=str))
    except Exception as error:
        print(f'Could not get log streamName: {error=}')
        print("Debugging message:")
        print(json.dumps(response, indent=4, default=str))

    build_status = response["buildBatches"][0]["buildBatchStatus"]
    if build_status == "SUCCEEDED":
        result = response["buildBatches"][0]["phases"]
        pprint(result)
        sys.exit(0)
    elif build_status == "IN_PROGRESS":
        pass
    else:
        result = response["buildBatches"][0]["phases"]
        pprint(result)
        sys.exit(1)

    time.sleep(5)

