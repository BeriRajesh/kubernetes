#!/bin/bash
set -e

# #### no need to modify below this comment ####

# # dowload script
# SCRIPT_NAME=bamboo-deploy.sh
# git archive --remote=git@bitbucket.org:annalect/devops.git release -- ${SCRIPT_NAME} | tar -xO > ${SCRIPT_NAME}
# chmod +x ${SCRIPT_NAME}

# cat ${SCRIPT_NAME}

# # execute script
# # ./${SCRIPT_NAME}

ECS_REGION=${ECS_REGION:-"us-east-1"}
REPOSITORY_NAME=${REPOSITORY_NAME-}
BUILD_ENV=${BUILD_ENV-}

if [ -z "$ECS_REGION" ];then
	echo "Please specify 'ECS_REGION' as an environment variable"
	exit 1
fi

eval $(/usr/local/bin/aws ecr get-login --no-include-email --region "${ECS_REGION}")

if [ ! -z "$REPOSITORY_NAME" ]; then
	if [ ! -z "$BUILD_ENV" ]; then
		# DOING BACKUP OF CURRENTLY RUNNING IMAGE
		REPOSITORY_NAME=${REPOSITORY_NAME:-}
		if [ ! -z ${REPOSITORY_NAME} ]; then
			DATESTR=$(date +%Y%m%d_%H%M)
			aws ecr batch-get-image --repository-name ${REPOSITORY_NAME} --image-ids imageTag=latest-${BUILD_ENV} --query 'images[].imageManifest' --output text > manifest.json
			if [ -s manifest.json ]; then
				aws ecr put-image --repository-name ${REPOSITORY_NAME} --image-tag backup-${BUILD_ENV}-${DATESTR} --image-manifest file://manifest.json
			else
				echo "WARNING: No previous image to backup."
			fi
		fi
	else
		echo "WARNING: No BUILD_ENV variable specied. Not creating backup of ECR image"
	fi
else
	echo "WARNING: No REPOSITORY_NAME variable specied. Not creating backup of ECR image"
fi
