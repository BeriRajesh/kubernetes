#!/bin/bash
set -euo pipefail

# version 1.1 / Sept-25 2022
#   Developed custom lambda entrypoint


# Setting default values
RUN_SECRET_ENTRYPOINT=${RUN_SECRET_ENTRYPOINT:-false}
KEY_ID_ARN=${KMS_KEY_ID_ARN:-}
BUILD_ENV=${BUILD_ENV:-}
APP_NAME=${APP_NAME:-}
SERVEROVERRIDE_KEY=${SERVEROVERRIDE_KEY:-}
BITBUCKET_DEPLOYMENT_KEY=${BITBUCKET_DEPLOYMENT_KEY:-}
QUIET=${QUIET:-}
REGION=${REGION:-${AWS_REGION}}


CONFIG_PATH=${CONFIG_PATH:-"/serveroverride.cfg"}


if [ $# -ne 1 ]; then
  echo "entrypoint requires the handler name to be the first argument" 1>&2
  exit 142
fi

export _HANDLER="$1"
RUNTIME_ENTRYPOINT=/var/runtime/bootstrap


if [ "${RUN_SECRET_ENTRYPOINT}" == "false" ]; then
	echo "Not running secrets-entrypoint, instead executing Lambda function handler."
	exec $RUNTIME_ENTRYPOINT
	exit $?
fi


# Check that the environment variable has been set correctly
if [ -z "${BUILD_ENV}" ] && [ -z "${APP_NAME}" ]; then
  echo >&2 'error: missing required environment variables'
  exit 1
fi


#Print output for variables
echo BUILD_ENV="$BUILD_ENV"
echo APP_NAME="$APP_NAME"
echo DOCKER_CMD=${@:-}
# echo AWS_DEFAULT_REGION=$REGION

function get_serveroverride () {

	echo "Retrieving serveroverride from Systems Manager Parameter Store or Secrets Manager..."

	if [ -n "${SERVEROVERRIDE_KEY}" ] && [ ! -z "${AWS_LAMBDA_FUNCTION_NAME}" ]; then
		echo "Container running on Lambda"

		aws --output text ssm get-parameter \
		    --region ${REGION} \
		    --name "${SERVEROVERRIDE_KEY}" \
		    --with-decryption \
		    --query Parameter.Value | xargs -i"{}" echo -e "{}" > /tmp/serveroverride.cfg
	fi
}

# Retrieve SERVEROVERRIDE_KEY from ssm parameter store or secret manager
if [ "${RUN_SECRET_ENTRYPOINT}" == true ] && [ ! -z "${SERVEROVERRIDE_KEY}" ]; then
	get_serveroverride
fi

# Execute CMD

if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
  exec /usr/local/bin/aws-lambda-rie $RUNTIME_ENTRYPOINT
else
  exec $RUNTIME_ENTRYPOINT
fi

