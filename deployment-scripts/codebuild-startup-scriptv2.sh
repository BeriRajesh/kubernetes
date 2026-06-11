#!/bin/bash
mkdir -p ~/.ssh

# Bitbucket ReadOnly Permission
echo "$BITBUCKET_DEPLOYMENT_KEY" > ~/.ssh/id_rsa && chmod 600 ~/.ssh/id_rsa
cp ~/.ssh/id_rsa  docker-deployments.key
ssh-keygen -F bitbucket.org > /dev/null || ssh-keyscan bitbucket.org >>~/.ssh/known_hosts
aws --version


# Download Secret Entrypoint from a central location
if [ "${RUN_SECRET_ENTRYPOINT}" == true ] && grep -q "^ENTRYPOINT" Dockerfile ; then
    echo "ENTRYPOINT not specified in Dockerfile. So,"
    if [ -z "${LAMBDA_FUNCTION_NAME}" ]; then
        echo "non-lambda case:"
        echo "    1) Fetching 'secrets-entrypoint.sh' from vault,"
        echo "    2) Adding instruction to Dockerfile to copyfile inside docker image,"
        echo "    3) Adding instruction to Dockerfile to run file in ENTRYPOINT,"

        aws s3 cp s3://adt-automation/ecs/secrets-entrypoint.sh .
        echo "Injecting content to Dockerfile"
        echo "" >> Dockerfile
        echo "### DEVOPS CODE INJECTION" >> Dockerfile
        echo 'COPY secrets-entrypoint.sh /' >> Dockerfile
        echo 'RUN chmod +x /secrets-entrypoint.sh' >> Dockerfile
        echo 'ENTRYPOINT ["/secrets-entrypoint.sh"]' >> Dockerfile
    else
        echo "lambda case:"
        echo "    1) Fetching 'lambda-entrypoint-v1.sh' from vault,"
        echo "    2) Adding instruction to Dockerfile to copyfile inside docker image,"
        echo "    3) Adding instruction to Dockerfile to run file in ENTRYPOINT,"
        echo "    4) Making available SO to Lambda in ${CONFIG_PATH}"
        aws s3 cp s3://adt-automation/ecs/lambda-entrypoint-v1.sh lambda-entrypoint.sh
        echo "Injecting content to Dockerfile"
        echo "" >> Dockerfile
        echo "### DEVOPS CODE INJECTION" >> Dockerfile
        echo 'COPY lambda-entrypoint.sh /' >> Dockerfile
        echo 'RUN chmod +x /lambda-entrypoint.sh' >> Dockerfile
        CONFIG_PATH=${CONFIG_PATH:-"/serveroverride.cfg"}
        echo "Adding soft link for ${CONFIG_PATH}..."
        echo "RUN echo "### Serveroverride overrides serverbase"  > /tmp/serveroverride.cfg"  >> Dockerfile
        echo "RUN ln -s /tmp/serveroverride.cfg ${CONFIG_PATH}" >> Dockerfile
    fi
else
    echo "Either not running RUN_SECRET_ENTRYPOINT is true or ENTRYPOINT not specified in dockerfile"
fi


#####
# added 2021-01-12
# apt-get update # removed 2021-03-11
# apt-get install -y bc  # removed 2021-03-11
pip3 install 'awscli<2'  --upgrade
#####

# ECR Login
echo Logging in to Amazon ECR...
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin 661095214357.dkr.ecr.us-east-1.amazonaws.com

# Dockerhub Login
echo Logging in to DockerHub...
echo $DOCKERHUB_PASSWORD > .docker.key
docker login -u annalecttio --password-stdin < .docker.key
rm .docker.key

# Variables set
ECS_SERVICE_NAME=${ECS_SERVICE_NAME:="${APP_NAME}"-"${BUILD_ENV}"}
IMAGE_TAG=${IMAGE_TAG:=latest-"${CODEBUILD_SOURCE_VERSION}"}

echo ECS_SERVICE_NAME is $ECS_SERVICE_NAME
echo IMAGE_TAG is $IMAGE_TAG

export DOWNLOAD_LOCATION=${DOWNLOAD_LOCATION:-$(mktemp -d)}
./download-scripts.sh

echo "Startup script done!"