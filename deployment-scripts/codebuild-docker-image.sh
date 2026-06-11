#!/bin/bash
set -e

export IMAGE_REPO="${ECR_REPO:-$IMAGE_REPO}"
export REGISTRY_URL=${REGISTRY_URL:-"661095214357.dkr.ecr.us-east-1.amazonaws.com"}
export REPOSITORY_URI="${REGISTRY_URL}"/"${IMAGE_REPO}"
export IMAGE_TAG=${IMAGE_TAG:-latest-$CODEBUILD_SOURCE_VERSION}
export COMMIT_HASH="${COMMIT_HASH:-$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)}"
export ECS_SERVICE_NAME=${ECS_SERVICE_NAME:-"${APP_NAME}"-"${BUILD_ENV}"}
export BUILD_IMAGE="$APP_NAME:latest"
export ECR_ACCOUNT_ID="${ECR_ACCOUNT_ID:-$AWS_ACCOUNT_ID}"
export ECR_REGION="${ECR_REGION:-$AWS_DEFAULT_REGION}"
export DOCKERFILE=${DOCKERFILE_RELATIVE_PATH:-"Dockerfile"}

echo IMAGE_REPO is $IMAGE_REPO
echo "REPOSITORY_URI is ${REPOSITORY_URI}"
echo COMMIT_HASH is $COMMIT_HASH
echo IMAGE_TAG is $IMAGE_TAG
echo ECS_SERVICE_NAME is $ECS_SERVICE_NAME
echo ECR_ACCOUNT_ID is $ECR_ACCOUNT_ID
echo ECR_REGION is $ECR_REGION

#Docker Build
function build () {
    if [ "$UNIT_TESTS" = "true" ] || [ "$DEPLOY_CODE" = "true" ] ; then

        echo Building the Docker image...

        CACHE_FLAG=""
        if [ "${USE_IMAGE_CACHING}" = "true" ]; then
            CACHE_FLAG="--cache-from $REPOSITORY_URI:$IMAGE_TAG"
            docker pull $REPOSITORY_URI:$IMAGE_TAG || true
        fi

        docker build ${CACHE_FLAG} -t "${BUILD_IMAGE}" -f "${DOCKERFILE}" .

        if [ ! -z  "${SERVEROVERRIDE_KEY}" ] && [ ! -z  "${CONFIG_PATH}" ]; then
            echo Copying serveroverride to build image...
            echo "${SERVEROVERRIDE_KEY}" > /tmp/override.cfg
            container="tempcontainer"
            docker create --name "$container" "${BUILD_IMAGE}"
            docker cp /tmp/override.cfg "$container":"${CONFIG_PATH}"
            docker commit "$container" "${BUILD_IMAGE}"
            docker rm "$container"
            rm -f /tmp/override.cfg
        fi

        echo Tagging the new Docker image with tag ${COMMIT_HASH}...
        docker tag $BUILD_IMAGE $REPOSITORY_URI:$COMMIT_HASH
        #docker tag $BUILD_IMAGE $REPOSITORY_URI:latest

        echo Tagging the new Docker image with tag ${IMAGE_TAG}...
        docker tag $BUILD_IMAGE $REPOSITORY_URI:$IMAGE_TAG

    fi
}

# Docker Push
function push () {
    if [ "${DEPLOY_CODE}" = "true" ]; then

        PREVIOUS_IMAGE_NAME=${IMAGE_TAG/latest/previous}
        LATEST_IMAGE_NAME="${IMAGE_TAG}"

        echo Logging in to Amazon ECR...
        aws ecr get-login-password --region $ECR_REGION | docker login --username AWS --password-stdin $REGISTRY_URL

        echo "Starting backup."

        # echo "Removing tag ${PREVIOUS_IMAGE_NAME} from ${IMAGE_REPO}"
        # aws ecr batch-delete-image --repository-name "${IMAGE_REPO}" --image-ids imageTag="${PREVIOUS_IMAGE_NAME}"

        echo "Tagging ${LATEST_IMAGE_NAME} with ${PREVIOUS_IMAGE_NAME}."
        MANIFEST=$(aws ecr batch-get-image --repository-name "${IMAGE_REPO}" --registry-id "${ECR_ACCOUNT_ID}" --region $ECR_REGION --image-ids imageTag="${LATEST_IMAGE_NAME}" --output json | jq --raw-output --join-output '.images[0].imageManifest')
        aws ecr put-image --repository-name "${IMAGE_REPO}" --registry-id "${ECR_ACCOUNT_ID}" --image-tag "${PREVIOUS_IMAGE_NAME}" --region $ECR_REGION --image-manifest "$MANIFEST" > /dev/null || echo "Manifest already existed with tag?"

        echo "Backup complete."

        echo Pushing the new Docker image to ECR with tag ${IMAGE_TAG}...
        #pushing latest-develop
        docker push $REPOSITORY_URI:$IMAGE_TAG

        echo Pushing the new Docker image to ECR with tag ${COMMIT_HASH}...
        docker push $REPOSITORY_URI:$COMMIT_HASH
        #docker push $REPOSITORY_URI:latest

        echo  Writing image definitions file...
        printf '[{"name":"%s","imageUri":"%s"}]' "$ECS_SERVICE_NAME" "$REPOSITORY_URI:$IMAGE_TAG" > imagedefinitions.json
    fi
}

function undo_latest_push () {

    # retagging image with tag previous-$BUILD_ENV to "latest-$BUILD_ENV", for example 'previous-develop' to 'latest-develop'

    PREVIOUS_IMAGE_NAME=${IMAGE_TAG/latest/previous}
    LATEST_IMAGE_NAME=${IMAGE_TAG}

    echo Logging in to Amazon ECR...
    aws ecr get-login-password --region $ECR_REGION | docker login --username AWS --password-stdin $REGISTRY_URL

    echo "Undoing latest ECR push"
    echo "Retagging ${PREVIOUS_IMAGE_NAME} to ${LATEST_IMAGE_NAME}"

    MANIFEST=$(aws ecr batch-get-image --repository-name "${IMAGE_REPO}" --registry-id "${ECR_ACCOUNT_ID}" --region $ECR_REGION --image-ids imageTag="${PREVIOUS_IMAGE_NAME}" --output json | jq --raw-output --join-output '.images[0].imageManifest')
    aws ecr put-image --repository-name "${IMAGE_REPO}" --registry-id "${ECR_ACCOUNT_ID}" --image-tag "${LATEST_IMAGE_NAME}" --region $ECR_REGION --image-manifest "$MANIFEST"  > /dev/null || echo "Manifest already existed with tag?"

    echo 'Undo complete'

}

# Excute called function
$1

# End of Script
