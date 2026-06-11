#!/bin/bash
RUN_SECRET_ENTRYPOINT=${RUN_SECRET_ENTRYPOINT:-true}
BUILD_ENV=${BUILD_ENV:-}
APP_NAME=${APP_NAME:-}
AWS_REGION=${AWS_REGION:-}


CONFIG_PATH=${CONFIG_PATH:-"serveroverride.cfg"}
# Fetch the value from SSM Parameter Store
SSM_PARAM=$(aws ssm get-parameter --name "$BUILD_ENV/$APP_NAME/serveroverride" --region "$AWS_REGION" --with-decryption --query "Parameter.Value" --output text)

# Write the fetched value to a file or export it as an environment variable
echo "$SSM_PARAM" > /serveroverride_key.cfg
# OR export as an environment variable:
# export SERVEROVERRIDE_KEY="$SSM_PARAM"

# Start the actual application
exec "$@"