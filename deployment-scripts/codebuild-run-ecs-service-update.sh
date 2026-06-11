#!/bin/bash
set -e

## environment variable set up in Bamboo plan

#### Some possible environment variables:
## Optional variables
# AWS_DEFAULT_REGION="us-east-1"
# APP_NAME=omni-portal

## Required variables
# Examples
# ECS_CLUSTER=andems-dev
# BUILD_ENV=dev 
# ECS_SERVICE_NAME      = "poc-shashi"
# ECS_TASK_FAMILY       = "poc-shashi"

export ECS_SERVICE_NAME=${ECS_SERVICE_NAME:-"${APP_NAME}"-"${BUILD_ENV}"}
export ECS_TASK_FAMILY=${ECS_TASK_FAMILY:-"${APP_NAME}"-"${BUILD_ENV}"}

echo ECS_SERVICE_NAME is $ECS_SERVICE_NAME
echo ECS_TASK_FAMILY is $ECS_TASK_FAMILY

# if [ -z "${ECS_SERVICE_NAME}" ]; then ECS_SERVICE_NAME="${APP_NAME}"-"${BUILD_ENV}"; fi
# if [ -z "${ECS_TASK_FAMILY}" ]; then ECS_TASK_FAMILY="${APP_NAME}"-"${BUILD_ENV}"; fi


####

# REMEMBER TO:
# 1. keep space between variables
# 2. Change approproate environment and ecs cluster name
###

# #### no need to modify below this comment ####

# # dowload script
# SCRIPT_NAME=codebuild-run-ecs-service-update.sh
# git archive --remote=git@bitbucket.org:annalect/devops.git release -- ${SCRIPT_NAME} | tar -xO > ${SCRIPT_NAME}
# chmod +x ${SCRIPT_NAME}

# cat ${SCRIPT_NAME}

# # execute script
# # ./${SCRIPT_NAME}

#### no need to modify below this comment ####

if [ "${DEPLOY_ECS_SERVICE}" = "true" ]; then
	echo "Running as: '$(whoami)'"

	DESIRED_COUNT=`aws --region "${AWS_DEFAULT_REGION}" ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE_NAME} | egrep "desiredCount" | head -1 | tr "/" " " | awk '{print $2}' | sed 's/,$//'`

	if [ "${DESIRED_COUNT}" = "0" ]; then
	    DESIRED_COUNT="1"
	fi

	aws ecs update-service --region "${AWS_DEFAULT_REGION}" --cluster "${ECS_CLUSTER}" --service "${ECS_SERVICE_NAME}" --task-definition "${ECS_TASK_FAMILY}" --desired-count "${DESIRED_COUNT}" --force-new-deployment
fi

# End of Script
