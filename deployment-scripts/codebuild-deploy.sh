#!/bin/bash
set -x

export REPOSITORY_URI="${REGISTRY_URL}"/"${IMAGE_REPO}"
export IMAGE_TAG=${IMAGE_TAG:-latest-$CODEBUILD_SOURCE_VERSION}
export ECS_SERVICE_NAME=${ECS_SERVICE_NAME:-"${APP_NAME}"-"${BUILD_ENV}"}
export ECS_TASK_FAMILY=${ECS_TASK_FAMILY:-"${APP_NAME}"-"${BUILD_ENV}"}

echo "REPOSITORY_URI is ${REPOSITORY_URI}"
echo IMAGE_TAG is $IMAGE_TAG
echo ECS_SERVICE_NAME is $ECS_SERVICE_NAME
echo ECS_TASK_FAMILY is $ECS_TASK_FAMILY

AWS_DEPLOY_REGION=${AWS_DEPLOY_REGION:-"${AWS_DEFAULT_REGION}"}
INVALIDATION_PATH=${INVALIDATION_PATH:-"/*"}


function lambda () {

    if [ -f Dockerfile  ] && grep -q "### DEVOPS CODE INJECTION" Dockerfile; then
        echo "Removing code injection and rebuilding Dockerfile"
        sed -i '/### DEVOPS CODE INJECTION/Q' Dockerfile

        echo "Rebuilding Dockerfile without injection"
        ./codebuild-docker-image.sh build

        echo "Pushing image to ECR"
        ./codebuild-docker-image.sh push

        echo "Image pushed."
    fi

    if [ ! "${DEPLOY_CODE}" = "true" ]; then
        echo "Variable DEPLOY_CODE is '$DEPLOY_CODE' so not updating ecs"
        return
    fi

    LAMBDA_FUNCTION_NAME=${LAMBDA_FUNCTION_NAME:-"${APP_NAME}"-"${BUILD_ENV}"}

    CURRENT_VERSION=$(aws --output json lambda get-function --function-name ${LAMBDA_FUNCTION_NAME} --qualifier release  --query Configuration.Version)

    # updating code n times
    set +ex
    n=2

    echo "Executing update-function-code '$n' times"
    aws sts get-caller-identity
    while [ $n -gt 0 ]; do
        aws lambda update-function-code \
                --function-name ${LAMBDA_FUNCTION_NAME} \
                --image-uri "${REPOSITORY_URI}:${IMAGE_TAG}" \
                --publish > OUTPUT

        exit_code=$?
        echo "exit code was: $exit_code"
        echo "output was:"
        cat OUTPUT
        if [ "$exit_code" -eq 0 ]; then
            n=$(($n-1))
            echo "Executing $n more times"
        fi
        sleep 5
    done
    set -e

    NEW_VERSION=$(cat OUTPUT | jq -r .Version)

    echo "upgrading from '${CURRENT_VERSION}' to '${NEW_VERSION}'..."

    until aws lambda update-alias --function-name ${LAMBDA_FUNCTION_NAME} --name release --function-version ${NEW_VERSION} --routing-config AdditionalVersionWeights={}; do
        echo "waiting to update the function"
        sleep 5;
    done;
}

function ecs() {
    if [ "${DEPLOY_CODE}" = "true" ]; then
        echo "Running as: '$(whoami)'"

        DESIRED_COUNT=`aws --region "${AWS_DEPLOY_REGION}" ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE_NAME} | egrep "desiredCount" | head -1 | tr "/" " " | awk '{print $2}' | sed 's/,$//'`

        if [ "${DESIRED_COUNT}" = "0" ]; then
            DESIRED_COUNT="1"
        fi

        aws ecs update-service --region "${AWS_DEPLOY_REGION}" --cluster "${ECS_CLUSTER}" --service "${ECS_SERVICE_NAME}" --task-definition "${ECS_TASK_FAMILY}" --desired-count "${DESIRED_COUNT}" --force-new-deployment
    else
        echo "Variable DEPLOY_CODE is '$DEPLOY_CODE' so not updating ecs"
    fi
}
imageTag=$IMAGE_TAG

function sam() {
    if [ "${DEPLOY_CODE}" = "true" ]; then
        echo "Running as: '$(whoami)'"
        #eval ${PARAMETERS_OVERRIDES}
        #if [ -z "$imageTag" ]; then imageTag=${IMAGE_TAG}; fi
        # if [ -z "$APP_NAME" ]; then APP_NAME=${latest-$CODEBUILD_SOURCE_VERSION}; fi
        # if [ -z "$BUILD_ENV" ]; then BUILD_ENV=${latest-$CODEBUILD_SOURCE_VERSION}; fi
        #PARAMS=${PARAMETERS_OVERRIDES}
        #echo ${PARAMS}
        #TAGS=${TAG_OVERRIDES}
        #echo ${TAGS}
        STACK_NAME=${APP_NAME}-${BUILD_ENV}

        echo "---------------------------------------------------------------------------------"

        echo "Started deploying ${STACK_NAME} resources..."

        echo "---------------------------------------------------------------------------------"

        SAM=$(which sam)

        ${SAM} --version

        ${SAM} build --config-env ${BUILD_ENV}

        ${SAM} deploy --stack-name ${STACK_NAME} --s3-bucket ${ARTIFACTS_BUCKET} \
             --s3-prefix ${APP_NAME}-${BUILD_ENV} \
             --role-arn ${DEPLOY_ROLE} \
             --capabilities CAPABILITY_IAM --region ${AWS_REGION} \
             --config-env ${BUILD_ENV} \
             --no-confirm-changeset \
             --no-fail-on-empty-changeset \
             --profile ${APP_NAME}

         echo "$(date):create:${STACK_NAME}:success"

         echo "---------------------------------------------------------------------------------"

         echo "End deployed ${STACK_NAME} resources successfully..."

         echo "---------------------------------------------------------------------------------"

    fi

}

function s3cdn() {
    . ./assume-role.sh set

    if [ "${DEPLOY_CODE}" = "true" ] && [ ! -z "${SOURCE_BUILD_PATH}" ]; then
        aws s3 cp ./${SOURCE_BUILD_PATH} ${S3_DEPLOY_PATH} --recursive --region "${AWS_DEPLOY_REGION}" --endpoint-url https://s3.us-east-1.amazonaws.com

        if [ "${INVALIDATE_CACHE}" = "true" ] && [ ! -z "${CF_DISTRIBUTION_ID}" ]; then
            aws cloudfront create-invalidation --distribution-id ${CF_DISTRIBUTION_ID} --paths "${INVALIDATION_PATH}"
        fi
    else
        if [  -f demo.html ]; then aws s3 cp ./demo.html ${S3_DEPLOY_PATH}/demo.html; fi || true

    fi

}

# Excute called function
$1