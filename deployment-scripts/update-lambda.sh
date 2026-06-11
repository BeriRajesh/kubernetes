#!/bin/bash
set -e

DOCKER_DEPLOYMENT_KEY_PATH_USER=${1:-}

LAMBDA_NAME=${LAMBDA_NAME:-}
BUILD_ENV=${BUILD_ENV:-}

echo $LAMBDA_NAME
echo $BUILD_ENV

# $(echo ${repo} | cut -d/ -f2 | cut -d. -f1)
if [ -z "${LAMBDA_NAME}" ]; then
    echo "ERROR: Please specify a LAMBDA_NAME as an environment variable."
    exit 1
fi
if [ -z "${BUILD_ENV}" ]; then
    echo "ERROR: Please specify a BUILD_ENV as an environment variable."
    exit 1
fi

LAMBDA_NAME="${LAMBDA_NAME}-${BUILD_ENV}"

echo "Deploying LAMBDA_NAME: ${LAMBDA_NAME}"

# if [ "$LAMBDA_NAME" == "sso_api" ]; then
#     LAMBDA_NAME="mssql-test"
#     echo "temporarily using name $LAMBDA_NAME for lambda function name"
# fi

ZIP_NAME="${LAMBDA_NAME}.zip"

DOCKER_DEPLOYMENT_KEY_PATH=docker-deployments.key
if [ ! -f "$DOCKER_DEPLOYMENT_KEY_PATH" ]; then
    if [ -z $DOCKER_DEPLOYMENT_KEY_PATH_USER ]; then
        echo "ERROR: Please specify the path for the deployment key as a first parameter. Eg. ./$0 /path/to/deployment_key.ext"
        exit 1
    fi
    if [ ! -f $DOCKER_DEPLOYMENT_KEY_PATH_USER ]; then
        echo "ERROR: Key not found at path: $DOCKER_DEPLOYMENT_KEY_PATH_USER"
        exit 1
    fi

    echo "Found key in: $DOCKER_DEPLOYMENT_KEY_PATH_USER"
    cp $DOCKER_DEPLOYMENT_KEY_PATH_USER $DOCKER_DEPLOYMENT_KEY_PATH
fi

./install-dependencies-lambda.sh "${DOCKER_DEPLOYMENT_KEY_PATH}"

UNZIPPED_SIZE=$(du -s --exclude=.git | head -n1 | awk '{print $1}')
if [ ${UNZIPPED_SIZE} -gt 249000000 ]; then
    echo "ERROR: Unzipped size is ${UNZIPPED_SIZE} whic is greater than 249M"
    exit 1
fi

chmod a+r -R *

echo "Compressing lambda code..."
zip -qr9 $ZIP_NAME .

echo "Removing unneeded files..."
zip -qd $ZIP_NAME \
    .git \
    update-lambda.sh \
    install-dependencies-lambda.sh

DESTINATION_S3="s3://annalect-deployment-artifacts/${LAMBDA_NAME}/"
echo "Uploading zip ..."
aws s3 --no-progress cp ${ZIP_NAME} ${DESTINATION_S3}

echo "Updating lambda code..."
aws lambda update-function-code \
    --function-name ${LAMBDA_NAME} \
    --s3-bucket annalect-deployment-artifacts \
    --s3-key ${LAMBDA_NAME}/${ZIP_NAME} \
    --publish \
    --cli-connect-timeout 6000

# echo "Updating lambda alias..."
# aws lambda update-alias \
#     --function-name "${LAMBDA_NAME}" \
#     --name "${BUILD_ENV}" \
#     --function-version "$MY_ALIAS"

echo "Process finished without errors"