#!/bin/bash
mkdir -p ~/.ssh

# Bitbucket ReadOnly Permission
echo "$BITBUCKET_DEPLOYMENT_KEY" > ~/.ssh/id_rsa && chmod 600 ~/.ssh/id_rsa
cp ~/.ssh/id_rsa  docker-deployments.key
ssh-keygen -F bitbucket.org > /dev/null || ssh-keyscan bitbucket.org >>~/.ssh/known_hosts
aws --version

# Download Secret Entrypoint from a central location
if [ "${RUN_SECRET_ENTRYPOINT}" == true ] && [ -z "${LAMBDA_FUNCTION_NAME}" ]; then
    if grep "^ENTRYPOINT" Dockerfile ; then
        echo "^ENTRYPOINT specified"
    else
        echo "^Entrypoint not specified"
        aws s3 cp s3://adt-automation/ecs/secrets-entrypoint.sh .

        echo "Injecting content to Dockerfile"
        echo "" >> Dockerfile
        echo "### DEVOPS CODE INJECTION" >> Dockerfile
        echo 'COPY secrets-entrypoint.sh /' >> Dockerfile
        echo 'RUN chmod +x /secrets-entrypoint.sh' >> Dockerfile
        echo 'ENTRYPOINT ["/secrets-entrypoint.sh"]' >> Dockerfile
    fi
    
    elif [ "${RUN_SECRET_ENTRYPOINT}" == true ] && [ ! -z "${LAMBDA_FUNCTION_NAME}" ]; then
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
# 2022-04-25: Shashi and An dont know what $VAULT is for, so disabling meanwhile
# if [ "${RUN_SECRET_ENTRYPOINT}" == true ] && [ -z "${VAULT}" ]; then

# ECR Login
echo Logging in to Amazon ECR...
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin 661095214357.dkr.ecr.us-east-1.amazonaws.com

# Dockerhub Login
echo Logging in to DockerHub...
echo $DOCKERHUB_PASSWORD > .docker.key
docker login -u annalecttio --password-stdin < .docker.key
rm .docker.key

# pip3 install git+ssh://git@bitbucket.org/annalect/pylect-infra.git@v.1.x

#####
# added 2021-01-12
# apt-get update # removed 2021-03-11
# apt-get install -y bc  # removed 2021-03-11
pip3 install 'awscli<2'  --upgrade
#####


# Download build scripts for devops repo in bitbucket
# Setup initial configuration for CodeBuild including ECR Login, copy Bitbucket Deploying key
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-run-code-minification.sh | tar -xO > codebuild-run-code-minification.sh
chmod u+x codebuild-run-code-minification.sh

# Pre-deployment script
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-pre_build.sh | tar -xO > codebuild-pre_build.sh
chmod u+x codebuild-pre_build.sh

#Sanity-Test Script
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-run-sanity-tests.sh | tar -xO > codebuild-run-sanity-tests.sh
chmod u+x codebuild-run-sanity-tests.sh

#Selenium-Test Script
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-run-selenium-tests.sh | tar -xO > codebuild-run-selenium-tests.sh
chmod u+x codebuild-run-selenium-tests.sh

#Pytest-Test Script
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-run-pytest.sh | tar -xO > codebuild-run-pytest.sh
chmod u+x codebuild-run-pytest.sh

#Pytest-Test Script V1
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-run-pytestv1.sh | tar -xO > codebuild-run-pytestv1.sh 
chmod u+x codebuild-run-pytestv1.sh

#Skip-Test Script
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-skip-test.sh | tar -xO > codebuild-skip-test.sh
chmod u+x codebuild-skip-test.sh

# Builds docker image and pushes Docker Image to ECR
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-docker-image.sh | tar -xO > codebuild-docker-image.sh
chmod u+x codebuild-docker-image.sh

# Updates ECS Service
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-run-ecs-service-update.sh | tar -xO > codebuild-run-ecs-service-update.sh
chmod u+x codebuild-run-ecs-service-update.sh

# RUN DB Deploy via any ORM tool on ECS Task Run
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-db-migrate.sh | tar -xO > codebuild-db-migrate.sh
chmod u+x codebuild-db-migrate.sh

# Updates Lambda function
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-run-lambda-update.sh | tar -xO > codebuild-run-lambda-update.sh
chmod u+x codebuild-run-lambda-update.sh

# updates Lambda or ECS service
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-deploy.sh | tar -xO > codebuild-deploy.sh
chmod u+x codebuild-deploy.sh

git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-deployv1.sh | tar -xO > codebuild-deployv1.sh
chmod u+x codebuild-deployv1.sh

# downloads codebuild-run_sql_deploy.py to deploy SQL script on container
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-run_sql_deploy_command.py | tar -xO > codebuild-run_sql_deploy_command.py

#downloads assume-role.sh
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/assume-role.sh | tar -xO > assume-role.sh
chmod u+x assume-role.sh

# Variables set
ECS_SERVICE_NAME=${ECS_SERVICE_NAME:="${APP_NAME}"-"${BUILD_ENV}"}
IMAGE_TAG=${IMAGE_TAG:=latest-"${CODEBUILD_SOURCE_VERSION}"}

echo ECS_SERVICE_NAME is $ECS_SERVICE_NAME
echo IMAGE_TAG is $IMAGE_TAG


# END
