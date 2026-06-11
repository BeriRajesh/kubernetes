""" script to trigger a codebuild project """

import os
import sys
import time

import boto3


# Optional Variables - APP_NAME and IMAGE_REPO to be set on Terraform code for the project
# APP_NAME
# IMAGE_REPO
# getCodeVersion
# GRUNTFILE=""

# Required Variables - These needs to be set as Bamboo variables
# CODEBUILD_PROJECT_NAME
# BUILD_ENV
# ECS_CLUSTER
# IMAGE_TAG
# DOCKER_PUSH
# DEPLOY_ECS_SERVICE
# MINIFY_CODE=true
# GRUNT_MINIFY_CODE=false
# UNIT_TESTS
# PERFORMANCE_TESTS
# CONFIG_PATH
# RUN_SECRET_ENTRYPOINT
# GET_APPS_SECRETS
# GET_ENV_SECRETS

# environment variable set up in Bamboo plan

CODEBUILD_PROJECT_NAME = os.environ.get("CODEBUILD_PROJECT_NAME") # ex:= <projectname>
BUILD_ENV              = os.environ.get("BUILD_ENV") # ex: dev
APP_NAME               = os.environ.get("APP_NAME") # ex: omni-portal
IMAGE_REPO             = os.environ.get("IMAGE_REPO") # ex: "annalect/poc"
IMAGE_TAG              = os.environ.get("IMAGE_TAG") # ex: "latest-develop"
CONFIG_PATH            = os.environ.get("CONFIG_PATH") # ex: "/serveroverride.cfg"
RUN_SECRET_ENTRYPOINT  = os.environ.get("RUN_SECRET_ENTRYPOINT") # ex: "false"
GET_APPS_SECRETS       = os.environ.get("GET_APPS_SECRETS") # ex: "false"
GET_ENV_SECRETS        = os.environ.get("GET_ENV_SECRETS") # ex: "false"
UNIT_TESTS             = os.environ.get("UNIT_TESTS") # ex: "false"
PERFORMANCE_TESTS      = os.environ.get("PERFORMANCE_TESTS") # ex: "false"
GRUNT_MINIFY_CODE      = os.environ.get("GRUNT_MINIFY_CODE") # ex: "false"
MINIFY_CODE            = os.environ.get("MINIFY_CODE") # ex: "false"
DOCKER_PUSH            = os.environ.get("DOCKER_PUSH") # ex: "false"
DEPLOY_ECS_SERVICE     = os.environ.get("DEPLOY_ECS_SERVICE") # ex: "false"
ECS_CLUSTER            = os.environ.get("ECS_CLUSTER") # ex: "andems-dev"


codebuild = boto3.client('codebuild')

# launch project
response = codebuild.start_build_batch(
    projectName=CODEBUILD_PROJECT_NAME
)

build_id = response["buildBatch"]["id"]

while True:
    response = codebuild.batch_get_build_batches(
        ids=[build_id]
    )

    build_status = response["buildBatches"][0]["buildBatchStatus"]
    print('Build status is {}'.format(build_status), flush=True)

    if build_status == "SUCCEEDED":
        sys.exit(0)
    elif build_status == "IN_PROGRESS":
        pass
    else:
        sys.exit(1)

    time.sleep(5)
